from spectradb.dataloaders import FluorescenceDataLoader, NMRDataLoader, FTIRDataLoader


def test_NMR_valid_file_format(txt_file):
    dataloader = NMRDataLoader(filepath=txt_file)
    assert dataloader.filepath == txt_file

def test_NMR_data(txt_file): 
    dataloader = NMRDataLoader(filepath=txt_file)
    assert dataloader.data == [5000.0, 5500.0]