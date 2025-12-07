from pathlib import Path
import shutil
import tempfile

import pytest

from miniature_sorter.artist_connectors.cast_n_play import CastNPlayConnector
from miniature_sorter.constants import PROJECT_ROOT
from miniature_sorter.rar_handler import RarHandler


def build_test_folder(
    paths_list: list[Path],
    target_folder: Path,
) -> None:
    for file_path in paths_list:
        shutil.copytree(
            file_path,
            target_folder / file_path.name,
        )


def test_ok_model_extraction():
    file_path = Path("/media/mnt/cast_n_play/1015_Zombified Dwarf")
    expected = "1015. Zombified Dwarf"
    assert expected == CastNPlayConnector._gather_filename(file_path)


def test_multiple_underscores_in_model_name():
    file_path = Path("/media/mnt/cast_n_play/1015_Zombified_Dwarf")
    with pytest.raises(ValueError):
        CastNPlayConnector._gather_filename(file_path)


def test_dot_name_model_extraction():
    file_path = Path("/media/mnt/cast_n_play/1015. Zombified Dwarf")
    expected = "1015. Zombified Dwarf"
    assert expected == CastNPlayConnector._gather_filename(file_path)


def test_valid_image_detection():
    file_path = PROJECT_ROOT / "release/22. Mimic"
    expected = file_path / "Mimic_CastnPlay.png"
    assert expected == CastNPlayConnector.detect_image_location(file_path)


@pytest.mark.skip
def test_image_is_being_moved():
    file_path = PROJECT_ROOT / "release/test_miniature/1014_Zombified Elf"
    CastNPlayConnector(general_output_location=PROJECT_ROOT / "result", rar_handler=RarHandler()).process_model_folder(
        file_path,
    )


@pytest.mark.skip
def test_throwback():
    file_path = PROJECT_ROOT / "release"
    CastNPlayConnector().process_throwback(
        file_path,
        PROJECT_ROOT / "result",
    )


def test_mixed_separation():
    filename = "22. Mimic"
    file_to_test = PROJECT_ROOT / "release" / filename
    with tempfile.TemporaryDirectory() as temp_input:
        with tempfile.TemporaryDirectory() as temp_output:
            temp_input = Path(temp_input)
            temp_output = Path(temp_output)

            build_test_folder([file_to_test], temp_input)
            output_model_location = temp_output / "Presupported"
            output_model_location.mkdir(exist_ok=True, parents=True)

            CastNPlayConnector()._process_supported(temp_input / filename, temp_output)

            file_structure = [
                temp_output / "Presupported/22. Mimic/Models/STL/Mimic_Supported.stl",
                temp_output / "Presupported/22. Mimic/Models/CHITU/Mimic_Supported.chitubox",
            ]

            for single_file in file_structure:
                assert single_file.exists(), f"{single_file} not found!"


def test_separate_lys_no_stl_folder():
    filename = "60_Ghosts"
    file_to_test = PROJECT_ROOT / "release" / filename
    with tempfile.TemporaryDirectory() as temp_input:
        with tempfile.TemporaryDirectory() as temp_output:
            temp_input = Path(temp_input)
            temp_output = Path(temp_output)

            build_test_folder([file_to_test], temp_input)
            output_model_location = temp_output / "Presupported"
            output_model_location.mkdir(exist_ok=True, parents=True)

            CastNPlayConnector()._process_supported(temp_input / filename, temp_output)

            file_structure = [
                temp_output / "Presupported/60. Ghosts/Models/STL/STL_Ghost_A_Supported.stl",
                temp_output / "Presupported/60. Ghosts/Models/STL/STL_Ghost_B_Supported.stl",
                temp_output / "Presupported/60. Ghosts/Models/LYS/LYS_Ghost_A_Supported.lys",
                temp_output / "Presupported/60. Ghosts/Models/LYS/LYS_Ghost_B_Supported.lys",
            ]

            for single_file in file_structure:
                assert single_file.exists(), f"{single_file} not found!"
