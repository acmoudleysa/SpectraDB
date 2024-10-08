import sqlite3
import json
from spectradb.dataloaders import (FTIRDataLoader, FluorescenceDataLoader,
                                   NMRDataLoader)
from typing import Union, List
from pathlib import Path
from spectradb.types import DataLoaderType
from contextlib import contextmanager
from datetime import datetime
from dataclasses import dataclass


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
                 table_name: str = "Measurements"
                 ) -> None:
        self.database = database
        self.table_name = table_name
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
        query1 = """

        INSERT OR IGNORE INTO instrument_sample_count (instrument_type, counter
        ) VALUES (?, 0)
        """
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
            commit: bool = True
    ) -> None:

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

    def to_csv(self) -> None:
        ...


@dataclass(slots=True)
class DummyClass:
    """
    A dummy class to handle fluorescence data.
    Since fluorescence data comes with multiple rows, ensuring that they are handled properly.  # noqa: E501
    One class per row.
    """
    data: List
    metadata: dict
    instrument_id: str
    filepath: str
