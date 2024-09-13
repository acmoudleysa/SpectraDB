from typing import Dict
import pandas as pd
from spectradb.base import BaseDataLoader, InstrumentID, metadata_template
from dataclasses import dataclass
from typing import ClassVar, Optional
import numpy as np 


@dataclass
class FluorescenceDataLoader(BaseDataLoader): 
    """
    Dataclass for loading and managing fluorescence data.

    This class inherits from BaseDataLoader and specifically handles fluorescence
    data, including validation, loading, and metadata extraction from CSV files.
    
    Attributes:
        filepath (Path): The path to the CSV file containing the data.
        data (Dict): A dictionary where keys are sample names, and values are 
            the corresponding fluorescence data (excitation along the rows and emission along columns).
        metadata (Dict): A dictionary containing metadata about the fluorescence 
            data, including signal metadata (wavelengths and sample information).
        instrument_id (InstrumentID): Class variable indicating the instrument type 
            used for fluorescence measurements.
        df (pd.DataFrame): DataFrame for structured data representation. Combines data and metadata
    """

    instrument_id: ClassVar[InstrumentID] = InstrumentID.Fluorescence.value

    def __post_init__(self):
        """
        Called automatically after the class is initialized.

        This method calls the parent class's `__post_init__` method, validates the data 
        to ensure it's in the correct format, and loads the data from the CSV file.
        """
        super().__post_init__()
        self._sample_id_map = {}  # Dictionary to store sample name -> ID mapping
        self.validate_data()
        self.load_data()

    def load_data(self) -> Dict:
        """
        Load fluorescence data from the CSV file and extract sample-specific metadata.
        """
        df = (pd.read_csv(self.filepath)
              .dropna(how="all", axis=1)
              .dropna(how="all", axis=0))

        unique_samples = set([col.split("_EX_")[0] for col in df.columns if "_EX_" in col])
        
        for sample_number, sample in enumerate(unique_samples, start=1):
            sample_id = f"S{sample_number}"
            self._sample_id_map[sample_id] = sample

            # Extracting emission wavelengths and excitation wavelengths
            if sample_number == 1:
                em_wl = df.iloc[1:, 0].astype(float).astype(int).tolist()
                idx, ex_wl = zip(*[[i+1, wavelengths.split("_EX_")[-1].split(".")[0]]
                                for i, wavelengths in enumerate(df.columns) if sample + "_EX_" in wavelengths])
            else:
                idx = (i for i, _ in enumerate(df.columns) if sample + "_EX_" in _)

            # Using metadata template function to create the metadata entry
            self.metadata[sample_id] = metadata_template(
                filepath=str(self.filepath),
                sample_name=sample,
                signal_metadata={
                    "Excitation": np.array(ex_wl, dtype=int).tolist(),
                    "Emission": em_wl
                }
            )

            # Storing actual fluorescence data for each sample
            self.data[sample_id] = df.iloc[1:, list(idx)].to_numpy(dtype=np.float32).T.tolist()

        print(self)

    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from the loaded fluorescence data.
        """
        data = list()
        for sample_id, metadata in self.metadata.items(): 
            metadata.update({"Data": self.data[sample_id]})
            data.append(metadata)
            
        self._df = pd.DataFrame(data, 
                            columns=["Filename", 
                                     "Measurement Date", 
                                     "Sample name", 
                                     "Internal sample code", 
                                     "Collected by", 
                                     "Comments", 
                                     "Data", 
                                     "Signal Metadata"])
        
        return self._df

    def add_metadata(self,  
                     identifier: str, 
                     sample_name: Optional[str] = None, 
                     internal_code: Optional[str] = None, 
                     collected_by: Optional[str] = None, 
                     comments: Optional[str] = None):
        """
        Add or update metadata for a given sample identifier.
        """
        if identifier not in self.metadata:
            raise KeyError(f"Sample identifier '{identifier}' not found.")
        
        sample_metadata = self.metadata[identifier]
        if sample_name is not None:
            sample_metadata['Sample name'] = sample_name
        if internal_code is not None:
            sample_metadata['Internal sample code'] = internal_code
        if collected_by is not None:
            sample_metadata['Collected by'] = collected_by
        if comments is not None:
            sample_metadata['Comments'] = comments


    def validate_data(self):
        """
        Validate the input file type.

        This method checks whether the input file is a CSV. If not, it raises a ValueError.

        Raises:
            ValueError: If the input file is not a CSV.
        """
        if self.filepath.suffix.lower() != ".csv": 
            raise ValueError("Invalid file extension! Make sure the data being fed is a CSV.")
        

    def __str__(self):
        """
        String representation of the object, showing sample IDs and their corresponding names in a table format with borders.
        """
        header = f"| {'Identifier':<15} | {'Sample Name':<50} |"
        separator = '+' + '-' * (len(header) - 2) + '+'
        
        sample_rows = [f"| {sample_id:<15} | {sample_name:<50} |" 
                    for sample_id, sample_name in self._sample_id_map.items()]
        
        table = f"{separator}\n{header}\n{separator}\n" + "\n".join(sample_rows) + f"\n{separator}"
        
        return f"FluorescenceDataLoader:\nFile: {self.filepath.stem}\nSamples:\n{table}"


    @property
    def df(self): 
        return self._create_dataframe()


if __name__ == "__main__": 
    test = FluorescenceDataLoader(filepath=r"C:\Users\amulya.baniya\Desktop\Github\ibet-olive-project\data\Fluorescence\Cuvettes_new\Cuv7_29_04_24.csv")
    test.add_metadata("S1")