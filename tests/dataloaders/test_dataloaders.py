from spectradb.dataloaders import FluorescenceDataLoader, NMRDataLoader, FTIRDataLoader
from datetime import datetime
import os 
from numpy.testing import assert_array_almost_equal
import pytest


class TestNMRDataLoader: 
    @pytest.fixture(autouse=True)
    def setup(self, txt_file, wrong_format): 
        self.txt_file = txt_file
        self.wrong_format = wrong_format
        self.dataloader = NMRDataLoader(filepath=txt_file)

    def test_NMR_valid_file_format(self):
        assert self.dataloader.filepath == self.txt_file

    def test_NMR_data(self): 
        assert self.dataloader.data == [5000.0, 5500.0]

    def test_NMR_metadata(self): 
        assert_array_almost_equal(
            self.dataloader.metadata["Signal Metadata"]['ppm'], 
            [16.4, 16.3]) 
        
        del self.dataloader.metadata['Signal Metadata']

        assert self.dataloader.metadata == {
            "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(self.txt_file)).strftime("%Y-%m-%d"), 
            "Filename": "example.txt", 
            "Sample name": None, 
            "Internal sample code": None, 
            "Collected by": None, 
            "Comments": None}

    def test_NMR_invalid_file_format(self): 
        with pytest.raises(ValueError, match="Invalid file extension! Make sure the data being fed has extension .txt"): 
            NMRDataLoader(filepath=self.wrong_format)



class TestFluorescenceDataLoader(): 
    @pytest.fixture(autouse=True)
    def setup(self, csv_file): 
        self.dataloader = FluorescenceDataLoader(csv_file)
        self.csv_file = csv_file

    def test_FL_valid_file_format(self):
        assert self.dataloader.filepath == self.csv_file

    def test_FL_data(self): 
        assert_array_almost_equal(self.dataloader.data['S1'], [[2.941176414, 2.915452003, 0], 
                        [2.673796892, 4.950494766, -4.889975548]])
        
        assert_array_almost_equal(self.dataloader.data['S2'], [[2.958580017, 8.902077675, 0],
                        [4.866179943, 0, -7.211538315]])
        
        assert_array_almost_equal(self.dataloader.data['S3'], [[2.949852467, 0, 0], 
                        [4.819277287, 7.462686539, -2.347417831]])
        
        assert_array_almost_equal(self.dataloader.data['S4'], [[18.34862328, 0, 0], 
                        [4.796163082, 4.878048897, 0]])

    

