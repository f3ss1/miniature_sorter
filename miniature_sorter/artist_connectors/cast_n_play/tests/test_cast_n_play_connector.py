from pathlib import Path

import pytest

from miniature_sorter.artist_connectors.cast_n_play import CastNPlayConnector
from miniature_sorter.constants import PROJECT_ROOT
from miniature_sorter.rar_handler import RarHandler


def test_ok_model_extraction():
    file_path = Path("/media/mnt/cast_n_play/1015_Zombified Dwarf")
    expected = "1015. Zombified Dwarf"
    assert expected == CastNPlayConnector._gather_filename(file_path)


def test_multiple_underscores_in_model_name():
    file_path = Path("/media/mnt/cast_n_play/1015_Zombified_Dwarf")
    with pytest.raises(ValueError):
        CastNPlayConnector._gather_filename(file_path)


def test_valid_image_detection():
    file_path = PROJECT_ROOT / "test_miniature/1014_Zombified Elf"
    expected = file_path / "1014_CastnPlay_ZombifiedElf.jpg"
    assert expected == CastNPlayConnector.detect_image_location(file_path)


def test_image_is_being_moved():
    file_path = PROJECT_ROOT / "test_miniature/1014_Zombified Elf"
    CastNPlayConnector(year_month="2025.11", rar_handler=RarHandler()).process_model_folder(file_path)
