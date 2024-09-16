from spectradb.dataloaders import FluorescenceDataLoader, NMRDataLoader, FTIRDataLoader
from datetime import datetime
import os 
from numpy.testing import assert_array_almost_equal


def test_NMR_valid_file_format(txt_file):
    dataloader = NMRDataLoader(filepath=txt_file)
    assert dataloader.filepath == txt_file

def test_NMR_data(txt_file): 
    dataloader = NMRDataLoader(filepath=txt_file)
    assert dataloader.data == [5000.0, 5500.0]

def test_NMR_metadata(txt_file): 
    dataloader = NMRDataLoader(filepath=txt_file)
    assert_array_almost_equal(
        dataloader.metadata["Signal Metadata"]['ppm'], 
        [16.4, 16.3]) 
    
    del dataloader.metadata['Signal Metadata']

    assert dataloader.metadata == {
        "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(txt_file)).strftime("%Y-%m-%d"), 
        "Filename": "example.txt", 
        "Sample name": None, 
        "Internal sample code": None, 
        "Collected by": None, 
        "Comments": None}
