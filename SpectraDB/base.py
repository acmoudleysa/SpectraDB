from pathlib import Path
from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
from datetime import datetime
import os


class InstrumentID(Enum):
    """
    Enum class that stores the id of the instruments
    """
    FTIR = "INS_1"
    NMR = "INS_2"
    Fluorescence = "INS_3"
    GC = "INS_4"


@dataclass
class BaseDataLoader(ABC):
    """
    Abstract base class for data loaders.

    Defines the essential methods and attributes for concrete data loader implementations.
    
    Attributes:
        filepath (Path): Path to the data file.
        data (Dict): Dictionary to store loaded data.
        df (pd.DataFrame): DataFrame for structured data representation.
        metadata (Dict): Dictionary to store metadata information.
    """
    
    filepath: Path
    data: Dict = field(init=False, default_factory=dict)
    _df: pd.DataFrame = field(init=False, default=None)
    metadata: Dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """
        Post-initialization checks for filepath.
        Ensures filepath is a string or Path object.
        """
        if not isinstance(self.filepath, (str, Path)):
            raise TypeError(f"Expected filepath to be of type str or Path, got {type(self.filepath).__name__}")
        self.filepath = Path(self.filepath)

    @abstractmethod
    def load_data(self) -> Dict:
        """
        Load data from the specified file.

        Returns:
            Dict: A dictionary containing the loaded data.
        """
        pass 

    @abstractmethod
    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a DataFrame from the loaded data and metadata.

        Returns:
            pd.DataFrame: A DataFrame representation of the data.
        """
        pass 

    @abstractmethod
    def add_metadata(self):
        """
        Add or update metadata for the loaded data.

        This method should be implemented to handle metadata changes or additions.
        """
        pass 

    @abstractmethod
    def validate_data(self):
        """
        Validate the data file and format.

        Raises:
            ValueError: If the data file is invalid or has an incorrect format.
        """
        pass

    @property
    @abstractmethod
    def df(self) -> pd.DataFrame:
        """
        Property to access the DataFrame. Creates or updates it if it doesn't exist.

        Returns:
            pd.DataFrame: The DataFrame representation of the data.
        """
        pass


def metadata_template(filepath: str, 
                      sample_name: str, 
                      internal_code: Optional[str] = "NA", 
                      collected_by: Optional[str] = "NA", 
                      comments: Optional[str] = "NA",
                      signal_metadata: Optional[Dict] = None) -> dict:
    """
    Generate a metadata template for a given sample.

    Args:
        filepath (str): The path to the file used to retrieve the measurement date.
        sample_name (str): The name of the sample.
        internal_code (str, optional): Internal sample code. Defaults to "NA".
        collected_by (str, optional): Name of the person who collected the data. Defaults to "NA".
        comments (str, optional): Additional comments about the sample. Defaults to "NA".
        signal_metadata (dict, optional): Signal metadata including excitation and emission wavelengths.

    Returns:
        dict: A dictionary containing the metadata template.
    """
    return {
        "Measurement Date": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d"),
        "Filename": os.path.basename(filepath),
        "Sample name": sample_name,
        "Internal sample code": internal_code,
        "Collected by": collected_by,
        "Comments": comments,
        "Signal Metadata": signal_metadata or {
            "Excitation": [],
            "Emission": []
        }
    }