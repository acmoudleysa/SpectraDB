from typing import Dict
import pandas as pd
from spectradb.dataloaders.base import (BaseDataLoader, InstrumentID,
                                        metadata_template)
from dataclasses import dataclass, field
from typing import ClassVar, Optional, List
import numpy as np
from io import StringIO
import csv


@dataclass(slots=True)
class FluorescenceDataLoader(BaseDataLoader):
    """
    Dataclass for loading and managing fluorescence data.

    This class inherits from BaseDataLoader and specifically handles
    fluorescence data, including validation, loading,
    and metadata extraction from CSV files.

    Attributes:
        filepath (Path): The path to the CSV file containing the data.
        data (Dict): A dictionary where keys are sample names, and values are
            the corresponding fluorescence data
            - (excitation along the rows and emission along columns).
        metadata (Dict): A dictionary containing metadata about the
            fluorescence data, including signal metadata
            - (wavelengths and sample information).
        instrument_id (InstrumentID): Class variable indicating the instrument
          type used for fluorescence measurements.
        df (pd.DataFrame): DataFrame for structured data representation.
    """

    instrument_id: ClassVar[InstrumentID] = InstrumentID.Fluorescence.value
    _sample_id_map: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """
        Called automatically after the class is initialized.

        This method calls the parent class's `__post_init__` method.
        """
        super(FluorescenceDataLoader, self).__post_init__()
        # Check this https://docs.python.org/3/library/dataclasses.html

    def load_data(self) -> Dict:
        """
        Load fluorescence data from the CSV file and extract sample metadata.
        """
        with open(self.filepath, "r") as rawfile:
            reader = csv.reader(rawfile)
            # Reading the header of the csv
            header = next(reader)
            # This part of the code is written to catch an edge case where the
            # user inputs a name with comma, causing the read_csv to fail
            correct_header = []
            current_data = []
            for data in header:
                if data == "":
                    if current_data:
                        correct_header.append(",".join(current_data))
                        current_data = []
                    correct_header.append(data)
                else:
                    current_data.append(data)
            # creating a stream because we wanna save the file in memoery
            output = StringIO()
            writer = csv.writer(output)
            # writing the first row
            writer.writerow(correct_header)
            # The reader is at the first row of data (after the header),
            # so we can write the remaining rows directly.
            writer.writerows(reader)
            # Reset the stream so that read_csv can read from the beginning
            output.seek(0)

        df = (pd.read_csv(output)
              .dropna(how="all", axis=1)
              .dropna(how="all", axis=0))

        # Getting the names of the samples that were analyzed.
        # Preferred over `set` as it preserves order.
        unique_samples = list(dict.fromkeys([col.split("_EX_")[0].strip()
                                            for col in df.columns
                                            if "_EX_" in col]))

        for sample_number, sample in enumerate(unique_samples, start=1):
            sample_id = f"S{sample_number}"
            self._sample_id_map[sample_id] = sample

            # Extracting emission wavelengths and excitation wavelengths
            if sample_number == 1:
                em_wl = df.iloc[1:, 0].astype(float).astype(int).tolist()
                idx, ex_wl = zip(*[[i+1, wavelengths.split("_EX_")[-1].split(".")[0]]  # noqa: E501
                                   for i, wavelengths in enumerate(df.columns)
                                   if sample + "_EX_" in wavelengths])
            else:
                idx = [i+1 for i, _ in enumerate(df.columns)
                       if sample + "_EX_" in _]

            # Using metadata template function to create the metadata entry
            self.metadata[sample_id] = metadata_template(
                filepath=self.filepath,
                sample_name=sample,
                signal_metadata={
                    "Excitation": np.array(ex_wl, dtype=int).tolist(),
                    "Emission": em_wl
                }
            )
            # Storing actual fluorescence data for each sample
            self.data[sample_id] = (df.iloc[1:, list(idx)]
                                    .to_numpy(dtype=np.float32)
                                    .T
                                    .tolist())

        print(self)

    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from the loaded fluorescence data.
        """
        data = list()
        for sample_id, metadata in self.metadata.items():
            data.append(metadata | {"Data": self.data[sample_id]})

        self._df = pd.DataFrame(data,
                                columns=["Filename",
                                         "Measurement Date",
                                         "Sample name",
                                         "Internal sample code",
                                         "Collected by",
                                         "Comments",
                                         "Data",
                                         "Signal Metadata"],
                                index=self.metadata.keys())
        return self._df

    def delete_measurement(self,
                           identifiers: str | List[str]) -> None:
        """
        Method to delete a measurement using identifier name
        """
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        non_existent = [id for id in identifiers if id not in self.metadata]
        if non_existent:
            raise KeyError(f"Sample identifier(s) not found: {', '.join(non_existent)}")  # noqa E501

        for identifier in identifiers:
            del self.metadata[identifier]
            del self.data[identifier]
            del self._sample_id_map[identifier]

    def add_metadata(self,
                     identifier: str,
                     sample_name: Optional[str] = None,
                     internal_code: Optional[str] = None,
                     collected_by: Optional[str] = None,
                     comments: Optional[str] = None) -> None:
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

    def validate_data(self) -> None:
        """
        Validate the input file type.

        This method checks whether the input file is a CSV.
        If not, it raises a ValueError.

        Raises:
            ValueError: If the input file is not a CSV.
        """
        if self.filepath.suffix.lower() != ".csv":
            raise ValueError("Invalid file extension! "
                             "Make sure the data being fed is a CSV.")

    def __str__(self) -> str:
        """
        String representation of the object, showing sample IDs and their
        corresponding names in a table format with borders.
        """
        header = f"| {'Identifier':<10} | {'Sample Name':<45} |"
        separator = '+' + '-' * (len(header) - 2) + '+'

        sample_rows = [f"| {sample_id:<10} | {sample_name:<45} |"
                       for sample_id, sample_name
                       in self._sample_id_map.items()]

        table = f"{separator}\n{header}\n{separator}\n" + "\n"\
            .join(sample_rows) + f"\n{separator}"

        return (f"Data generated from Agilent Cary Eclipse fluorescence "
                f"spectrometer\nFile: {self.filepath.stem}\nSamples:\n{table}")

    @property
    def df(self) -> pd.DataFrame:
        return self._create_dataframe()


@dataclass(slots=True)
class FTIRDataLoader(BaseDataLoader):
    """
    Data loader for FTIR data files.

    Attributes:
        filepath (Path): Path to the data file.
        data (Dict): Dictionary to store loaded data.
        df (pd.DataFrame): DataFrame for structured data representation.
        metadata (Dict): Dictionary to store metadata information.
        instrument_id (ClassVar[InstrumentID]): Identifier for the FTIR instrument.

    Methods:
        load_data(): Loads and processes FTIR data from a file.
        _create_dataframe(): Creates a DataFrame from the loaded data.
        add_metadata(sample_name=None, internal_code=None, collected_by=None, comments=None): Updates metadata.
        validate_data(): Validates the file extension.
    """  # noqa: E501

    instrument_id: ClassVar[InstrumentID] = InstrumentID.FTIR.value

    def __post_init__(self):
        super(FTIRDataLoader, self).__post_init__()

    def load_data(self) -> Dict:
        with open(self.filepath, "rb") as file:   # reading in binary
            # spectrum resolution
            file.seek(564)
            num_wn_points = np.fromfile(file, np.int32, 1)[0]

            # fetching the max and min wavenumbers
            file.seek(576)
            wavenumbers_max = np.fromfile(file, np.float32, 1)[0]
            wavenumbers_min = np.fromfile(file, np.float32, 1)[0]

            # Finding the place where the intensity starts
            file.seek(288)
            _check = 0
            while _check != 3:
                _check = np.fromfile(file, np.uint16, 1)[0]

            # Locate the intensity position
            file.seek(np.fromfile(file, np.uint16, 1)[0])
            self.data = np.fromfile(file, np.float32, num_wn_points).tolist()

            self.metadata = metadata_template(
                filepath=self.filepath,
                signal_metadata={
                    "Wavenumbers": np.linspace(wavenumbers_min,
                                               wavenumbers_max,
                                               num_wn_points)[::-1].astype(int).tolist()  # noqa: E501
                }
            )
        print(self)

    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from the loaded fluorescence data.
        """
        data = [self.metadata | {"Data": self.data}]
        self._df = pd.DataFrame(data,
                                columns=["Filename",
                                         "Measurement Date",
                                         "Sample name",
                                         "Internal sample code",
                                         "Collected by",
                                         "Comments",
                                         "Data",
                                         "Signal Metadata"],
                                index=pd.Index(["S1"]))
        return self._df

    def add_metadata(self,
                     sample_name: Optional[str] = None,
                     internal_code: Optional[str] = None,
                     collected_by: Optional[str] = None,
                     comments: Optional[str] = None) -> None:
        """
        Add or update metadata for a given sample identifier.
        """
        if sample_name is not None:
            self.metadata['Sample name'] = sample_name
        if internal_code is not None:
            self.metadata['Internal sample code'] = internal_code
        if collected_by is not None:
            self.metadata['Collected by'] = collected_by
        if comments is not None:
            self.metadata['Comments'] = comments

    def validate_data(self) -> None:
        if self.filepath.suffix.lower() != ".spa":
            raise ValueError("Invalid file extension! "
                             "Make sure the data being fed has extension .spa")

    def __str__(self) -> None:
        """
        String representation of the object
        """
        return f"Data generated from FTIR spectrometer\nFile: \
            {self.filepath.stem}"

    @property
    def df(self) -> pd.DataFrame:
        return self._create_dataframe()


@dataclass(slots=True)
class NMRDataLoader(BaseDataLoader):
    """
    Data loader for NMR data files in .txt format.

    Inherits from BaseDataLoader and specializes in handling NMR data.

    Attributes:
        filepath (Path): Path to the data file.
        data (Dict): Dictionary to store loaded data.
        df (pd.DataFrame): DataFrame for structured data representation.
        metadata (Dict): Dictionary to store metadata information.
        instrument_id (ClassVar[InstrumentID]): Identifier for the NMR instrument.  # noqa: E501

    Methods:
        load_data(): Loads and processes NMR data from a file.
        _create_dataframe(): Creates a DataFrame from the loaded data.
        add_metadata(sample_name=None, internal_code=None, collected_by=None, comments=None): Updates metadata.
        validate_data(): Validates the file extension.
    """

    instrument_id: ClassVar[InstrumentID] = InstrumentID.NMR.value

    def __post_init__(self):
        super(NMRDataLoader, self).__post_init__()

    def load_data(self) -> Dict:
        data = np.loadtxt(self.filepath, skiprows=1, delimiter=",")
        self.data = data[:, 1].astype(np.float32).tolist()
        self.metadata = metadata_template(
                filepath=self.filepath,
                signal_metadata={
                    "ppm": data[:, -1].astype(np.float32).tolist()
                }
            )
        print(self)

    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from the loaded fluorescence data.
        """
        data = [self.metadata | {"Data": self.data}]
        self._df = pd.DataFrame(data,
                                columns=["Filename",
                                         "Measurement Date",
                                         "Sample name",
                                         "Internal sample code",
                                         "Collected by",
                                         "Comments",
                                         "Data",
                                         "Signal Metadata"],
                                index=pd.Index(["S1"]))
        return self._df

    def add_metadata(self,
                     sample_name: Optional[str] = None,
                     internal_code: Optional[str] = None,
                     collected_by: Optional[str] = None,
                     comments: Optional[str] = None) -> None:
        """
        Add or update metadata for a given sample identifier.
        """
        if sample_name is not None:
            self.metadata['Sample name'] = sample_name
        if internal_code is not None:
            self.metadata['Internal sample code'] = internal_code
        if collected_by is not None:
            self.metadata['Collected by'] = collected_by
        if comments is not None:
            self.metadata['Comments'] = comments

    def validate_data(self) -> None:
        if self.filepath.suffix.lower() != ".txt":
            raise ValueError("Invalid file extension! "
                             "Make sure the data being fed has extension .txt")

    def __str__(self) -> None:
        """
        String representation of the object
        """
        return f"Data generated from Bruker NMR (in .txt format)\
              \nFile: {self.filepath.stem}"

    @property
    def df(self) -> pd.DataFrame:
        return self._create_dataframe()
