from typing import Union, Iterable
from spectradb.dataloaders import (FluorescenceDataLoader,
                                   FTIRDataLoader,
                                   NMRDataLoader)

FluorescenceIterable = Iterable[FluorescenceDataLoader]
FTIRIterable = Iterable[FTIRDataLoader]
NMRIterable = Iterable[NMRDataLoader]

DataLoaderIterable = Union[FluorescenceIterable, FTIRIterable, NMRIterable]
DataLoaderType = Union[FluorescenceDataLoader, FTIRDataLoader, NMRDataLoader]
