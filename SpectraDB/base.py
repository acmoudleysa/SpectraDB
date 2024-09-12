from pathlib import Path
from abc import ABC, abstractmethod
import pandas as pd
import json 
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict



class InstrumentID(Enum):
    """
    Enum class that stores the id of the instruments
    """
    FTIR = "Ins_1"
    NMR = "Ins_2"
    Fluorescence = "Ins_3"
    GC = "Ins_4"



@dataclass
class BaseDataLoader(ABC):
    """
    Abstract base class that defines how the main dataloader classes have to be implemented
    """
    filepath: Path
    data: Dict = field(init=False, default=None)
    df: pd.DataFrame = field(init=False, default=None)
    metadata: pd.DataFrame = field(init=False, default=None)

    def __post_init__(self): 
        if not isinstance(self.filepath, (str, Path)):
            raise TypeError(f"Expected filepath to be of type str or Path, got {type(self.filepath).__name__}")


    @abstractmethod
    def load_data(self) -> Dict: 
        pass 

    @abstractmethod
    def create_dataframe(self) -> pd.DataFrame: 
        pass 

    @abstractmethod
    def add_metadata(self): 
        pass 


    @abstractmethod
    def validate_data(self): 
        pass 
    