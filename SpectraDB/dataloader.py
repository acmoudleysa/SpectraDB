from typing import Dict
import pandas as pd
from spectradb.base import BaseDataLoader, InstrumentID
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass
class FluorescenceDataLoader(BaseDataLoader): 
    """
    Dataclass to create Fluorescence Data Object
    """

    instrument_id: ClassVar[InstrumentID] = InstrumentID.Fluorescence.value

    def __post_init__(self):
        super().__post_init__()
        self.filepath = Path(self.filepath)
        self.validate_data()
        
    def load_data(self) -> Dict:
        return super().load_data()
    
    def create_dataframe(self) -> pd.DataFrame:
        return super().create_dataframe()
    
    def add_metadata(self):
        return super().add_metadata()
    
    def validate_data(self):
        if self.filepath.suffix.lower() != ".csv": 
            raise ValueError("Invalid file extension! Make sure the data being fed is a CSV.")
        





if __name__ == "__main__": 
    test = FluorescenceDataLoader(filepath="")


