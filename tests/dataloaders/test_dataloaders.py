from spectradb.dataloaders import FluorescenceDataLoader, NMRDataLoader, FTIRDataLoader
from datetime import datetime
import os 
from numpy.testing import assert_array_almost_equal, assert_equal
import pytest
import numpy as np 


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


class TestFTIRDataLoader: 
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
    def setup(self, csv_file, wrong_format, edge_case_csv_file): 
        self.dataloader = FluorescenceDataLoader(csv_file)
        self.dataloader_edge_case = FluorescenceDataLoader(edge_case_csv_file)
        self.csv_file = csv_file
        self.wrong_format = wrong_format
        self.edge_case = edge_case_csv_file

    def test_FL_valid_file_format(self):
        assert self.dataloader.filepath == self.csv_file
        assert self.dataloader_edge_case.filepath == self.edge_case

    def test_FL_data(self): 
        for objs in [self.dataloader, self.dataloader_edge_case]: 
            assert_array_almost_equal(objs.data['S1'], [[2.941176414, 2.915452003, 0], 
                            [2.673796892, 4.950494766, -4.889975548]])
            
            assert_array_almost_equal(objs.data['S2'], [[2.958580017, 8.902077675, 0],
                            [4.866179943, 0, -7.211538315]])
            
            assert_array_almost_equal(objs.data['S3'], [[2.949852467, 0, 0], 
                            [4.819277287, 7.462686539, -2.347417831]])
            
            assert_array_almost_equal(objs.data['S4'], [[18.34862328, 0, 0], 
                            [4.796163082, 4.878048897, 0]])

    def test_FL_invalid_file_format(self):
        with pytest.raises(ValueError, match="Invalid file extension! Make sure the data being fed is a CSV"): 
            FluorescenceDataLoader(filepath=self.wrong_format)

    def test_FL_metadata(self): 
        for objs, file, name in zip([self.dataloader, self.dataloader_edge_case], 
                              [self.csv_file, self.edge_case], 
                              ["Test.csv", "edgecase_FL.csv"]):         
            assert objs.metadata["S2"] == {
                "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d"), 
                "Filename": name, 
                "Sample name": "Sample2", 
                "Internal sample code": None, 
                "Collected by": None, 
                "Signal Metadata": {
                    "Excitation": [200, 205], 
                    "Emission": [210, 215, 220]
                }, 
                "Comments": None}
            
            assert objs.metadata["S3"] == {
                "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d"), 
                "Filename": name, 
                "Sample name": "Sample3", 
                "Internal sample code": None, 
                "Collected by": None, 
                "Signal Metadata": {
                    "Excitation": [200, 205], 
                    "Emission": [210, 215, 220]
                }, 
                "Comments": None}
            
            assert objs.metadata["S4"] == {
                "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d"), 
                "Filename": name, 
                "Sample name": "Sample4", 
                "Internal sample code": None, 
                "Collected by": None, 
                "Signal Metadata": {
                    "Excitation": [200, 205], 
                    "Emission": [210, 215, 220]
                }, 
                "Comments": None}

        assert self.dataloader_edge_case.metadata["S1"] == {
            "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(self.edge_case)).strftime("%Y-%m-%d"), 
            "Filename": "edgecase_FL.csv", 
            "Sample name": "1,5,7 ABC", 
            "Internal sample code": None, 
            "Collected by": None, 
            "Signal Metadata": {
                "Excitation": [200, 205], 
                "Emission": [210, 215, 220]
            }, 
            "Comments": None}
        

        assert self.dataloader.metadata["S1"] == {
            "Measurement Date" : datetime.fromtimestamp(os.path.getmtime(self.csv_file)).strftime("%Y-%m-%d"), 
            "Filename": "Test.csv", 
            "Sample name": "Sample1", 
            "Internal sample code": None, 
            "Collected by": None, 
            "Signal Metadata": {
                "Excitation": [200, 205], 
                "Emission": [210, 215, 220]
            }, 
            "Comments": None}
        
    def test_delete_measurements(self): 
        self.dataloader.delete_measurement("S2")
        assert all("S2" not in d for d in [self.dataloader.data, self.dataloader.metadata, self.dataloader._sample_id_map])


    def test_add_metadata(self): 
        self.dataloader._create_dataframe()

        self.dataloader.add_metadata(
            identifier="S2", 
            sample_name="Check_sample", 
            internal_code="C1", 
            collected_by="XYZ", 
            comments="Just a test"
        )

        assert self.dataloader.metadata['S2']['Sample name'] == "Check_sample"
        assert self.dataloader.metadata['S2']['Internal sample code'] == "C1"
        assert self.dataloader.metadata['S2']['Collected by'] == "XYZ"
        assert self.dataloader.metadata['S2']['Comments'] == "Just a test"

        # This is important because the df won't be changed until the user calls the property `df`. 
        assert_equal(
            self.dataloader._df['Sample name'].to_numpy(), 
            np.array(["Sample1",
                    "Sample2", 
                    "Sample3", 
                    "Sample4"])
        )
        # since we are using df now, the property calls the internal _create dataframe and updates the dataframe. 
        # This is an intended behavior because spectradb uses dict and only creates dataframe when users asks for it. 

        assert_equal(
            self.dataloader.df['Sample name'].to_numpy(), 
            np.array(["Sample1",
                    "Check_sample", 
                    "Sample3", 
                    "Sample4"])
        )
