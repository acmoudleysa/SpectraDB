from spectradb.dataloaders import FluorescenceDataLoader, NMRDataLoader, FTIRDataLoader
import pytest

@pytest.fixture(scope="session")
def txt_file(tmp_path_factory): 
    file = tmp_path_factory.mktemp("data")/"example.txt"
    file.write_text("Title\n 1, 5000, 555, 16.4\n 2, 5500, 555, 16.3")
    return file 


@pytest.fixture(scope="session")
def wrong_format(tmp_path_factory): 
    file = tmp_path_factory.mktemp("data")/"example.wtf"
    return file