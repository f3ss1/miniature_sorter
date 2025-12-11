from pathlib import Path
import string
import re
from typing import Iterable, Collection
import shutil

from miniature_sorter import logger
from miniature_sorter.artist_connectors.exceptions import MultipleImagesFoundException, ImageNotFoundException


class BiteTheBulletConnector:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    MODEL_EXTENSIONS_MAP = {
        ".stl": "STL",
        ".lys": "LYS",
        ".chitubox": "CHITU",
    }
    PAREN_CONTENT = re.compile(r"\((.*?)\)")

    def __init__(
        self,
        presupported_files_location: str = "Pre-Supported",
    ) -> None:
        self.presupported_files_location = presupported_files_location

    @classmethod
    def _process_unsupported(
        cls,
        model_folder_path: Path,
        general_output_location: Path,
        root_folders_ignore: Iterable[str] | None,
        image_absolute_location: Path,
    ) -> None:
        if root_folders_ignore is None:
            root_folders_ignore = []

        model_name = cls._gather_filename(model_folder_path)

        output_model_location = general_output_location / "Unsupported" / model_name
        output_model_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        output_model_files_location = output_model_location / "Models"
        output_model_files_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        cls.extract_all_files_of_given_extension(
            folder_path=model_folder_path,
            extension=".stl",
            output_path=output_model_files_location / cls.MODEL_EXTENSIONS_MAP[".stl"],
            folders_to_remove=set(cls.MODEL_EXTENSIONS_MAP.values()),
        )

        shutil.copy2(
            src=image_absolute_location,
            dst=output_model_location / (model_name + image_absolute_location.suffix),
        )

    @staticmethod
    def extract_all_files_of_given_extension(
        folder_path: Path,
        extension: str,
        output_path: Path,
        folders_to_remove: Collection[str],
    ) -> bool:
        if not extension.startswith("."):
            extension = "." + extension

        files_with_extension_present = False
        for path in folder_path.rglob(f"*{extension}"):
            rel = path.relative_to(folder_path)
            filtered = [p for p in rel.parts if p not in folders_to_remove]
            rel = Path(*filtered)
            target = output_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            files_with_extension_present = True

        return files_with_extension_present

    @classmethod
    def _gather_filename(
        cls,
        filepath: Path,
    ) -> str:
        """Selects the actual name from the name of a folder with a model.
        Is expected to be used while iterating over folders in a months's folder.

        Parameters
        ----------
        filepath : Path

        Returns
        -------
        str
            The filename.

        """
        if filepath.name.lower().startswith("exotic"):
            inside_brackets_content = cls.PAREN_CONTENT.search(filepath.name.lower())
            if inside_brackets_content is None:
                logger.warning(f"Failed to find in-brackets content for exotic file: {filepath.name.lower()}")
                filename = filepath.name
            else:
                filename = inside_brackets_content
        else:
            filename = filepath.name

        return string.capwords(filename)

    @classmethod
    def detect_image_location(cls, filepath: Path) -> Path:
        logger.debug(f"Detecting images in {filepath}. List of directory: {list(filepath.iterdir())}")
        images_list = [f for f in filepath.iterdir() if f.suffix.lower() in cls.IMAGE_EXTENSIONS and f.is_file()]
        logger.debug(f"Found total {len(images_list)} images in {filepath}: {images_list}")

        main_images = [f for f in images_list if f.name.startswith("_")]

        if len(main_images) > 1:
            error_message = f"Found more than one image in {filepath}: {main_images}!"
            raise MultipleImagesFoundException(error_message)
        if len(main_images) == 0:
            error_message = f"Failed to find an image in {filepath}!"
            raise ImageNotFoundException(error_message)

        return main_images[0]
