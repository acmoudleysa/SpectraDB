from typing import Union
from spectradb.dataloaders import (FluorescenceDataLoader,
                                   FTIRDataLoader,
                                   NMRDataLoader)

DataLoaderType = Union[FluorescenceDataLoader, FTIRDataLoader, NMRDataLoader]
