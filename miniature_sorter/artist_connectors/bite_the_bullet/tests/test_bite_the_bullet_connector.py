import tempfile
from pathlib import Path
import shutil

from miniature_sorter import logger
from miniature_sorter.constants import PROJECT_ROOT
from miniature_sorter.artist_connectors.bite_the_bullet import BiteTheBulletConnector


def build_test_folder(
    paths_list: list[Path],
    target_folder: Path,
) -> None:
    for file_path in paths_list:
        shutil.copytree(
            file_path,
            target_folder / file_path.name,
        )


def get_file_tree(path: Path) -> list[Path]:
    result = []
    for p in path.rglob("*"):
        if p.is_file():
            result.append(p)

    return result


def test_valid_image_detection():
    file_path = PROJECT_ROOT / "small_release/bite_the_bullet/Elf Rogue"
    expected = file_path / "_2512_ch_elf_rogue.jpg"
    assert expected == BiteTheBulletConnector.detect_image_location(file_path)


def test_unsupported_processing():
    filename = "Elf Rogue"
    file_to_test = PROJECT_ROOT / "small_release/bite_the_bullet" / filename
    image_absolute_location = file_to_test / "_2512_ch_elf_rogue.jpg"

    with tempfile.TemporaryDirectory() as temp_input:
        with tempfile.TemporaryDirectory() as temp_output:
            temp_input = Path(temp_input)
            temp_output = Path(temp_output)

            build_test_folder([file_to_test], temp_input)
            output_model_location = temp_output / "Unsupported"
            output_model_location.mkdir(exist_ok=True, parents=True)

            BiteTheBulletConnector()._process_unsupported(
                temp_input / filename,
                temp_output,
                root_folders_ignore=None,
                image_absolute_location=image_absolute_location,
            )

            file_structure = [
                temp_output / "Unsupported/Elf Rogue/Models/STL/2512_ch_elf_rogue.stl",
                temp_output / "Unsupported/Elf Rogue/Models/STL/2512_ch_elf_rogue_b.stl",
                temp_output / "Unsupported/Elf Rogue/Elf Rogue.jpg",
            ]

            logger.debug(f"Resulting structure: {get_file_tree(temp_output)}")
            for single_file in file_structure:
                assert single_file.exists(), f"{single_file} not found!"
