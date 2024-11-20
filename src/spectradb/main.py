import sqlite3
import json
from spectradb.dataloaders import (FTIRDataLoader, FluorescenceDataLoader,
                                   NMRDataLoader)
from typing import Union, List, Literal, Optional
from pathlib import Path
from spectradb.types import DataLoaderType
from contextlib import contextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import os
import shutil


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
                 backup_interval: int = True,
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
        latest_backup = max(self.backup_dir.glob("*.sqlite"),
                            default=None,
                            key=os.path.getctime)

        if latest_backup:
            last_backup_time = datetime.fromtimestamp(
                os.path.getctime(latest_backup)
            )
            if (current_time - last_backup_time) < timedelta(hours=self.backup_interval):  # noqa E51
                return

        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{Path(self.database).stem}_periodic_backup_{timestamp}.sqlite"  # noqa E51
        backup_path = self.backup_dir/backup_filename

        try:
            shutil.copy2(self.database,
                         backup_path)
            self._manage_backups()
        except Exception as e:
            raise e

    def _manage_backups(self):
        backups = sorted(
            self.backup_dir.glob(
                f"{Path(self.database).stem}_periodic_backup_*"),
            key=os.path.getctime
        )
        while len(backups) >= self.max_backups:
            os.remove(backups.pop(0))

    def __create_table(self) -> None:
        """
        Creates a table in the SQLite database if it does not already exist.
        """
        query = f"""

        CREATE TABLE IF NOT EXISTS {self.table_name}_instrument_sample_count (
        instrument_type TEXT PRIMARY KEY,
        counter INTEGER DEFAULT 0
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
            signal_metadata TEXT,
            date_added TEXT,
            UNIQUE(instrument_id, sample_name, internal_code, comments)
        );

        CREATE TRIGGER IF NOT EXISTS generate_sample_id
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
        self._periodic_backup()

        if isinstance(obj, (FluorescenceDataLoader,
                            FTIRDataLoader,
                            NMRDataLoader)):
            obj = [obj]

        for idx_obj, instance in enumerate(obj):
            if isinstance(instance, FluorescenceDataLoader):
                obj.pop(idx_obj)
                for idx_sample, sample_id in enumerate(instance._sample_id_map):  # noqa: E501
                    dummy = DummyClass(
                        data=instance.data[sample_id],
                        metadata=instance.metadata[sample_id],
                        instrument_id=instance.instrument_id,
                        filepath=instance.filepath
                    )
                    obj.insert(idx_obj+idx_sample, dummy)

        entries = map(create_entries, obj)
        query1 = f"""
        INSERT OR IGNORE INTO {self.table_name}_instrument_sample_count (instrument_type, counter
        ) VALUES (?, 0)
        """  # noqa: E501
        query2 = f"""
        INSERT INTO {self.table_name} (
            instrument_id, measurement_date, sample_name,
            internal_code, collected_by, comments,
            data, signal_metadata, date_added
        ) VALUES (
            :instrument_id, :measurement_date, :sample_name,
            :internal_code, :collected_by, :comments,
            :data, :signal_metadata, :date_added
        )
        """
        with self._get_cursor() as cursor:
            cursor.executemany(query1, [(inst_ins.instrument_id,)
                                        for inst_ins in obj])
            if commit:
                self._connection.commit()

        with self._get_cursor() as cursor:
            cursor.executemany(query2, entries)
            if commit:
                self._connection.commit()

    def remove_sample(
            self,
            sample_id: Union[str, List[str]],
            *,
            commit: bool = False
    ) -> None:
        self._periodic_backup()

        if isinstance(sample_id, str):
            sample_id = [sample_id]
        query = f"""
            DELETE FROM {self.table_name}
            WHERE sample_id=?
            """

        with self._get_cursor() as cursor:
            cursor.executemany(
                query,
                ((id, ) for id in sample_id)
            )
            if commit:
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
                              table_name: str,
                              instrument_type: Literal['NMR', 'FTIR', 'FL']) -> pd.DataFrame:  # noqa: E501
        query = f"SELECT * FROM {table_name} WHERE instrument_id = ? ORDER BY measurement_id"  # noqa: E501
        with self._get_cursor() as cursor:
            cursor.execute(query, (instrument_type,))
            data = cursor.fetchall()
        return pd.DataFrame(data, columns=[col[0] for
                                           col in cursor.description])

    def fetch_sample_data(self,
                          table_name: str,
                          sample_info: str,
                          col_name: str = "sample_name") -> pd.DataFrame:
        if not isinstance(sample_info, str):
            sample_info = str(sample_info)

        query = f"SELECT * FROM {table_name} WHERE {col_name} = ?"
        with self._get_cursor() as cursor:
            cursor.execute(query, (sample_info,))
            data = cursor.fetchall()
        return pd.DataFrame(data, columns=[col[0] for
                                           col in cursor.description])

    def get_data_by_instrument_and_sample(self,
                                          table_name: str,
                                          instrument_type: Literal['NMR', 'FTIR', 'FL'],  # noqa: E501
                                          sample_name: str) -> pd.DataFrame:
        if not isinstance(sample_name, str):
            sample_name = str(sample_name)
        query = f"SELECT * FROM {table_name} WHERE instrument_id = ? AND sample_name = ?"  # noqa: E501
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


@dataclass(slots=True)
class DummyClass:
    """
    A dummy class to handle fluorescence data.
    Since fluorescence data comes with multiple rows, ensuring that they are handled properly.
    One class per row.
    """  # noqa: E501
    data: List
    metadata: dict
    instrument_id: str
    filepath: str
