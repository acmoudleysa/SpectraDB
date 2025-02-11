import sqlite3
import json
from spectradb.dataloaders import (FTIRDataLoader, FluorescenceDataLoader,
                                   NMRDataLoader)
from typing import Union, Literal, Optional, List
from pathlib import Path
from spectradb.types import DataLoaderType
from contextlib import contextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import os
import shutil
import numpy as np
from itertools import product
from spectradb.utils import spectrum, validate_dataframe
import plotly.graph_objects as go


def create_entries(obj):
    """
    Converts a data loader object into a dictionary suitable for database insertion.  # noqa: E501
    """
    return {
        "instrument_id": obj.instrument_id,
        "measurement_date": obj.metadata['Measurement Date'],
        "sample_name": obj.metadata["Sample name"]
        if obj.metadata['Sample name'] is not None else "",
        "internal_code": obj.metadata["Internal sample code"]
        if obj.metadata['Internal sample code'] is not None else "",
        "collected_by": obj.metadata["Collected by"]
        if obj.metadata['Collected by'] is not None else "",
        "comments": obj.metadata["Comments"]
        if obj.metadata['Comments'] is not None else "",
        "data": json.dumps(obj.data),
        "signal_metadata": json.dumps(obj.metadata["Signal Metadata"]),
        "date_added": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


class Database:
    """
    Spectroscopic SQLite database handler.
    """

    def __init__(self,
                 database: Union[Path, str],
                 table_name: str = "measurements",
                 backup: bool = True,
                 backup_interval: int = 12,
                 max_backups: int = 2
                 ) -> None:
        self.database = database
        self.table_name = table_name

        self.backup = backup
        self.backup_dir = Path(database).parent/"database_backup"
        self.backup_interval = backup_interval
        self.max_backups = max_backups
        if self.backup:
            Path.mkdir(self.backup_dir, exist_ok=True)

        self._connection = None

    def __enter__(self):
        self._connection = sqlite3.connect(self.database)
        self.__create_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            self._connection.close()

        self._connection = None

    @contextmanager
    def _get_cursor(self):
        """Context manager for database transactions."""
        if not self._connection:
            raise RuntimeError(
                "Database connection is not established. Use 'with' statement.")  # noqa E501

        cursor = self._connection.cursor()
        try:
            yield cursor

        except sqlite3.IntegrityError:
            print(
                "\033[91m"  # Red color start
                "┌───────────────────────────────────────────────┐\n"
                "│      ❗**Duplicate Entry Detected**❗        │\n"
                "│                                               │\n"
                "│ The data you're trying to add already exists. │\n"
                "│ Check the following for uniqueness:           │\n"
                "│ • Instrument ID                               │\n"
                "│ • Sample Name                                 │\n"
                "│ • Internal Sample Code                        │\n"
                "│                                               │\n"
                "│ Please update the information and try again.  │\n"
                "└───────────────────────────────────────────────┘\n"
                "\033[0m"  # Reset color
            )

            self._connection.rollback()

        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()

    def _periodic_backup(self):
        if not self.backup:
            return

        current_time = datetime.now()
        latest_backup = max(
            self.backup_dir.glob(f"{Path(self.database).stem}_periodic_backup_*"),  # noqa E501
            default=None,
            key=os.path.getctime
            )
        if latest_backup:
            last_backup_time = datetime.fromtimestamp(
                os.path.getctime(latest_backup)
            )
            if (current_time - last_backup_time) < timedelta(hours=self.backup_interval):  # noqa E501
                return

        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{Path(self.database).stem}_periodic_backup_{timestamp}.sqlite"  # noqa E501
        backup_path = self.backup_dir/backup_filename

        try:
            shutil.copy2(self.database, backup_path)
            self._manage_backups()
        except Exception as e:
            raise e

    def _manage_backups(self):
        backups = sorted(
            self.backup_dir.glob(
                f"{Path(self.database).stem}_periodic_backup_*"),
            key=os.path.getctime
        )
        if len(backups) > self.max_backups:
            os.remove(backups[0])

    def __create_table(self) -> None:
        """
        Creates a table in the SQLite database if it does not already exist.
        """
        trigger_name = (f"{self.table_name}_generate_sample_id"
                        if self.table_name != "measurements"
                        else "generate_sample_id")
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name}_instrument_sample_count (
        instrument_type TEXT PRIMARY KEY,
        counter INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS signal_metadata (
        metadata_id INTEGER PRIMARY KEY, -- Refer to this site https://www.sqlite.org/autoinc.html  # noqa E501
        metadata TEXT UNIQUE
        );


        CREATE TABLE IF NOT EXISTS {self.table_name} (
            measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id TEXT,
            instrument_id TEXT ,
            measurement_date TEXT,
            sample_name TEXT,
            internal_code TEXT,
            collected_by TEXT,
            comments TEXT,
            data TEXT,
            date_added TEXT,
            metadata_id INTEGER, -- Reference to signal_metadata table
            UNIQUE(instrument_id, sample_name, internal_code, comments)
        );

        CREATE TRIGGER IF NOT EXISTS {trigger_name}
        AFTER INSERT ON {self.table_name}
        BEGIN
            UPDATE {self.table_name}_instrument_sample_count
            SET counter = counter + 1
            WHERE instrument_type = NEW.instrument_id;

            UPDATE {self.table_name}
            SET sample_id = NEW.instrument_id || '_' ||
            (SELECT counter FROM {self.table_name}_instrument_sample_count
            WHERE instrument_type = NEW.instrument_id)
            WHERE rowid = NEW.rowid;
        END;

        """
        with self._get_cursor() as cursor:
            cursor.executescript(query)

    def add_sample(
            self,
            obj: Union[DataLoaderType, List[DataLoaderType]],
            *,
            commit: bool = True
    ) -> None:
        """
        Adds one or more samples to the database.

        Args:
            obj: A data loader object or iterable of data loader objects.
            commit: Whether to commit immediately.
        """

        if isinstance(obj, (FluorescenceDataLoader,
                            FTIRDataLoader,
                            NMRDataLoader)):
            obj = [obj]

        for idx_obj, instance in enumerate(obj):
            if isinstance(instance, FluorescenceDataLoader):
                obj.pop(idx_obj)
                for idx_sample, sample_id in enumerate(instance._sample_id_map):  # noqa: E501
                    # I can use the dataloader with with _load_data_on_init
                    # as False. But just to simplify things,
                    # I decided to use a simple DummyClass.
                    dummy = DummyClass(
                        data=instance.data[sample_id],
                        metadata=instance.metadata[sample_id],
                        instrument_id=instance.instrument_id,
                        filepath=instance.filepath
                    )
                    obj.insert(idx_obj+idx_sample, dummy)

        entries = list(map(create_entries, obj))
        query1 = f"""
                INSERT OR IGNORE INTO {self.table_name}_instrument_sample_count
                (instrument_type, counter)
                VALUES (?, 0)
                """

        query2 = """
                INSERT OR IGNORE INTO signal_metadata (metadata)
                VALUES (?)
                """

        query3 = f"""
        INSERT INTO {self.table_name} (
            instrument_id, measurement_date, sample_name,
            internal_code, collected_by, comments,
            data, date_added, metadata_id
        ) VALUES (
            :instrument_id, :measurement_date, :sample_name,
            :internal_code, :collected_by, :comments,
            :data, :date_added,
            (SELECT metadata_id FROM signal_metadata
            WHERE metadata = :signal_metadata)
        )
        """
        with self._get_cursor() as cursor:
            cursor.executemany(query1, [(inst_ins.instrument_id,)
                                        for inst_ins in obj])
            cursor.executemany(query2, [(entry['signal_metadata'],)
                                        for entry in entries])
            cursor.executemany(query3, entries)

            if commit:
                self._periodic_backup()
                self._connection.commit()

    def remove_sample(
            self,
            sample_id: str | List[str],
            *,
            commit: bool = False) -> None:

        if isinstance(sample_id, str):
            sample_id = [sample_id]

        # Create the placeholder string dynamically
        placeholders = ', '.join('?' for _ in sample_id)

        query = f"""
            DELETE FROM {self.table_name}
            WHERE sample_id IN ({placeholders})
        """

        with self._get_cursor() as cursor:
            cursor.execute(query, sample_id)
            if commit:
                self._periodic_backup()
                self._connection.commit()

    def open_connection(self) -> None:
        """Open a connection to the database."""
        if self._connection is not None:
            raise RuntimeError("Connection is already open.")
        self._connection = sqlite3.connect(self.database)
        self.__create_table()

    def close_connection(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def fetch_instrument_data(self,
                              instrument_type: Literal['NMR', 'FTIR', 'FL']) -> pd.DataFrame:  # noqa: E501
        query = f"SELECT * FROM {self.table_name} WHERE instrument_id = ? ORDER BY measurement_id"  # noqa: E501
        with self._get_cursor() as cursor:
            cursor.execute(query, (instrument_type,))
            data = cursor.fetchall()
        return pd.DataFrame(data, columns=[col[0] for
                                           col in cursor.description])

    def fetch_sample_data(self,
                          sample_info: str | List[str],
                          table_name: str = None,
                          col_name: str = "sample_name",
                          ordered: bool = False) -> pd.DataFrame:
        if isinstance(sample_info, str):
            sample_info = [sample_info]

        target_table = table_name or self.table_name
        # Base query preparation
        placeholders = ', '.join('?' for _ in sample_info)

        if ordered:
            # SQL with order preservation (slow)
            query = f"""
            SELECT *
            FROM {target_table}
            WHERE {col_name} IN ({placeholders})
            ORDER BY CASE {col_name}
                    {' '.join(f"WHEN '{sample}' THEN {i}" for
                              i, sample in enumerate(sample_info))}
                    END
            """
        else:
            # Standard query (much faster)
            query = f"""SELECT * FROM {target_table}
                    WHERE {col_name} IN ({placeholders})"""

        with self._get_cursor() as cursor:
            cursor.execute(query, tuple(sample_info))
            data = cursor.fetchall()

        return pd.DataFrame(data, columns=[col[0]
                                           for col in cursor.description])

    def get_data_by_instrument_and_sample(self,
                                          instrument_type: Literal['NMR', 'FTIR', 'FL'],  # noqa: E501
                                          sample_name: str) -> pd.DataFrame:
        if not isinstance(sample_name, str):
            sample_name = str(sample_name)
        query = f"SELECT * FROM {self.table_name} WHERE instrument_id = ? AND sample_name = ?"  # noqa: E501
        with self._get_cursor() as cursor:
            cursor.execute(query, (instrument_type, sample_name))
            data = cursor.fetchall()
        return pd.DataFrame(data, columns=[col[0] for
                                           col in cursor.description])

    def execute_custom_query(self,
                             query: str,
                             params: Optional[tuple] = None) -> tuple:
        if query.strip().lower().startswith("select"):
            with self._get_cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                column_names = [description[0] for description
                                in cursor.description]
                return results, column_names
        else:
            ValueError("Only SELECT queries are allowed with this method.")

    def transform_data_for_analysis(
            self,
            instrument_type: Literal["NMR",
                                     "FTIR",
                                     "FL"],
            sample_ids: List[str] = None,
            reference_sample_id: str = None,
            output_format: Literal["df",
                                   "csv"] = "df"
    ) -> dict | None:
        if sample_ids:
            df = self.fetch_sample_data(
                sample_info=sample_ids,
                col_name="sample_id"
            )
        else:
            df = self.fetch_instrument_data(instrument_type)

        instrument_config = {
            "NMR": "ppm",
            "FTIR": "Wavenumbers",
            "FL": ("Excitation", "Emission")}

        key = instrument_config[instrument_type]

        df = self._parse_data(df,
                              reference_sample_id,
                              key)

        if output_format == "csv":
            output_dir = Path(self.database).parent / "csv_export"
            output_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_dir / f"{instrument_type}.csv", index=False)
            return None

        return df

    def _parse_data(self,
                    df: pd.DataFrame,
                    reference_id: Optional[str],
                    metadata_key: str | tuple) -> pd.DataFrame:
        if reference_id:
            ref_sample = df[df.sample_id == reference_id].iloc[0]
            ref_metadata_id = ref_sample['metadata_id']
        else:
            ref_metadata_id = df.iloc[0]['metadata_id']
        query = """
            SELECT metadata
            FROM signal_metadata
            WHERE metadata_id = ?
            """
        with self._get_cursor() as cursor:
            cursor.execute(query, (int(ref_metadata_id),))
            ref_metadata = json.loads(cursor.fetchone()[0])

        if isinstance(metadata_key, tuple):
            ref_data = {key: ref_metadata[key] for key in metadata_key}
            columns = [
                f"{ex}EX/{em}EM"
                for ex, em in
                product(ref_data[metadata_key[0]], ref_data[metadata_key[1]])
                ]
            # is_valid = lambda meta: all(  # noqa E731
            #     len(meta[key]) == len(ref_data[key]) for key in metadata_key
            #     )
            transform_fn = lambda df: np.array(df  # noqa E731
                                               .data
                                               .map(json.loads)
                                               .tolist()
                                               ).reshape(df.shape[0],
                                                         -1)

        else:
            ref_data = ref_metadata[metadata_key]
            columns = ref_data
            # is_valid = lambda meta: len(meta[metadata_key]) == len(ref_data)  # noqa E731
            transform_fn = lambda df: np.vstack(df  # noqa E731
                                                .data
                                                .map(json.loads)
                                                .tolist())

        df_filtered = df[df['metadata_id'] == ref_metadata_id]

        try:
            data = transform_fn(df_filtered)
        except ValueError:
            raise ValueError("Unable to stack data array due to "
                             "inconsistent lengths")

        return pd.concat(
            objs=[df_filtered[['sample_name', 'internal_code']],
                  pd.DataFrame(data, columns=columns)],
            axis=1)

    @validate_dataframe
    def return_dataloader(self,
                          sample_ids: str | List[str],
                          table_name: str = None,
                          df: pd.DataFrame = None
                          ) -> (NMRDataLoader |
                                FTIRDataLoader |
                                FluorescenceDataLoader):
        if df is None:
            if sample_ids is None:
                raise ValueError("Either df or sample_ids must be provided")
            df = self.fetch_sample_data(
                sample_info=sample_ids,
                table_name=table_name
                if table_name is not None
                else self.table_name,
                col_name="sample_id",
                ordered=True
            )

        loaders = {
            "NMR": (NMRDataLoader, Path("dummy.txt")),
            "FL": (FluorescenceDataLoader, Path("dummy.csv")),
            "FTIR": (FTIRDataLoader, Path("dummy.spa")),
        }

        dataloaders = []

        query = """
            SELECT metadata
            FROM signal_metadata
            WHERE metadata_id = ?
            """
        for row in df.itertuples():
            ins_type = row.instrument_id

            with self._get_cursor() as cursor:
                cursor.execute(query, (int(row.metadata_id),))
                signal_metadata = json.loads(cursor.fetchone()[0])

            cls, dummyfile = loaders[ins_type]
            if ins_type in ["NMR", "FTIR"]:
                dummy_dl_ins = cls(dummyfile,
                                   _load_data_on_init=False)
                dummy_dl_ins.data = json.loads(row.data)

                with self._get_cursor() as cursor:
                    cursor.execute(query, (int(row.metadata_id),))
                    signal_metadata = json.loads(cursor.fetchone()[0])

                dummy_dl_ins.metadata = {
                    "Sample name": row.sample_name,
                    "Signal Metadata": signal_metadata
                }
                dataloaders.append(dummy_dl_ins)

            elif ins_type in ["FL"]:
                dummy_dl_ins = cls(dummyfile,
                                   _load_data_on_init=False)
                dummy_dl_ins.data['S1'] = json.loads(row.data)
                with self._get_cursor() as cursor:
                    cursor.execute(query, (int(row.metadata_id),))
                    signal_metadata = json.loads(cursor.fetchone()[0])
                dummy_dl_ins.metadata['S1'] = {
                        "Sample name": row.sample_name,
                        "Signal Metadata": signal_metadata
                    }
                dataloaders.append(dummy_dl_ins)

        if len(dataloaders) == 1:
            return dataloaders[0]

        return dataloaders

    def create_spectrum(self,
                        sample_ids: str | List[str] = None,
                        table_name: str = None,
                        df: pd.DataFrame = None,
                        fl_plot_type: Literal["1D", "2D"] = "2D"
                        ) -> go.Figure:
        dataloaders = self.return_dataloader(sample_ids=sample_ids,
                                             table_name=table_name,
                                             df=df)
        if not isinstance(dataloaders, list):
            dataloaders = [dataloaders]

        elif not all(isinstance(o, type(dataloaders[0])) for o in dataloaders):
            raise TypeError("Only one type of spectroscopic method allowed.")

        if isinstance(dataloaders[0],
                      (NMRDataLoader, FTIRDataLoader)):
            return spectrum(dataloaders)
        elif isinstance(dataloaders[0], FluorescenceDataLoader):
            objs = {f"obj{i}": obj for i, obj in enumerate(dataloaders,
                                                           start=1)}
            ids = {f"obj{i}": ["S1"]
                   for i in range(1, len(dataloaders)+1)}
            return spectrum(
                objs,
                identifier=ids,
                plot_type=fl_plot_type)


@dataclass(slots=True)
class DummyClass:
    """
    A dummy class to handle fluorescence data.
    Since fluorescence data comes with multiple rows, ensuring that they are handled properly.
    One class per row.
    """  # noqa: E501
    data: list
    metadata: dict
    instrument_id: str
    filepath: str
