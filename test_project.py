import pytest
from project import validate_masterpass
from project import open_vault
from project import save_vault


def test_validate_masterpass():
    assert validate_masterpass("1234Test1234!") == "1234Test1234!"

def test_open_vault():
    assert open_vault("nonexistent_file") == {}

def test_save_vault():
    vault = {"key":{1,2,3}}
    with pytest.raises(TypeError):
        save_vault(vault,"test.html")