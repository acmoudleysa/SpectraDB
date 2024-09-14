import sqlite3
import json
from spectradb.dataloaders import FTIRDataLoader, FluorescenceDataLoader, NMRDataLoader
from typing import Union
from pathlib import Path
from spectradb.types import DataLoaderType, DataLoaderIterable

def create_entries(obj): 
    """
    Converts a data loader object into a dictionary suitable for database insertion.
    """
    return {
        "instrument_id": obj.instrument_id,
        "measurement_date": obj.metadata['Measurement Date'], 
        "sample_name": obj.metadata["Sample name"], 
        "internal_code": obj.metadata["Internal sample code"], 
        "collected_by": obj.metadata["Collected by"], 
        "comments": obj.metadata["Comments"], 
        "data": json.dumps(obj.data), 
        "signal_metadata": json.dumps(obj.metadata["Signal Metadata"])
    }

class DataBase: 
    """
    Spectroscopic SQLite database handler.
    """

    def __init__(self, 
                 database: Union[Path, str], 
                 table_name: str = "Measurements"
                 ) -> None: 
        self.connection = sqlite3.connect(database)
        self.table_name = table_name
        self.__create_table()
        
    def __create_table(self): 
        """
        Creates a table in the SQLite database if it does not already exist.
        """
        self.connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id TEXT, 
                measurement_date TEXT, 
                sample_name TEXT, 
                internal_code TEXT, 
                collected_by TEXT, 
                comments TEXT, 
                data TEXT,           
                signal_metadata TEXT 
            )
            """
        )

    def add_sample(
            self, 
            obj: Union[DataLoaderType, DataLoaderIterable], 
            *, 
            commit: bool = True
    ): 
        """
        Adds one or more samples to the database.

        Args:
            obj: A data loader object or iterable of data loader objects.
            commit: Whether to commit immediately.
        """
        if isinstance(obj, (FluorescenceDataLoader, FTIRDataLoader, NMRDataLoader)): 
            obj = [obj] 

        entries = map(create_entries, obj)
        
        self.connection.executemany(
            f"""
            INSERT INTO {self.table_name} (
                instrument_id, measurement_date, sample_name, 
                internal_code, collected_by, comments, 
                data, signal_metadata
            ) VALUES (
                :instrument_id, :measurement_date, :sample_name, 
                :internal_code, :collected_by, :comments, 
                :data, :signal_metadata
            )
            """, 
            entries
        )

        if commit: 
            self.connection.commit()
