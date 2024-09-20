import pytest
from pathlib import Path

path = Path(__file__).parent


@pytest.fixture(scope="session")
def txt_file(tmp_path_factory):
    file = tmp_path_factory.mktemp("data")/"example.txt"
    file.write_text("Title\n 1, 5000, 555, 16.4\n 2, 5500, 555, 16.3")
    return file


@pytest.fixture(scope="session")
def wrong_format(tmp_path_factory):
    file = tmp_path_factory.mktemp("data")/"example.wtf"
    return file


@pytest.fixture
def csv_file():
    return path/"Test.csv"


@pytest.fixture(scope="session")
def edge_case_csv_file(tmp_path_factory):
    with open(path/"Test.csv", "r") as readfile:
        contents = readfile.read()
        contents = contents.replace("Sample1", "1,5,7 ABC")
    file = tmp_path_factory.mktemp("data")/"edgecase_FL.csv"
    file.write_text(contents)
    return file


@pytest.fixture(scope="session")
def spa_file(tmp_path_factory):
    pass
