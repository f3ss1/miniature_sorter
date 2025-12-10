from copy import deepcopy
from pathlib import Path
import shutil
from collections.abc import Iterable, Collection

from miniature_sorter import logger
from miniature_sorter.artist_connectors.exceptions import (
    ImageNotFoundException,
    MultipleImagesFoundException,
    ModelNameDetectionException,
)


class CastNPlayConnector:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    MODEL_EXTENSIONS_MAP = {
        ".stl": "STL",
        ".lys": "LYS",
        ".chitubox": "CHITU",
    }

    def __init__(
        self,
        presupported_files_location: str = "Pre-Supported",
    ) -> None:
        self.presupported_files_location = presupported_files_location

    def process_models(
        self,
        models_path: Path,
        output_path: Path,
        details_dict: dict[str, list[str]] | None = None,
    ) -> None:
        details_dict = self.normalize_details(details_dict)
        reversed_details_dict = self.reverse_dict_with_list_values(details_dict)
        self.prepare_folders(output_path, details_dict)

        for model_folder in self._iter_model_folders(models_path):
            model_type = reversed_details_dict.get(model_folder.name, "Characters")
            self.process_single_model_folder(model_folder, output_path / model_type)

    def process_single_model_folder(
        self,
        model_folder_path: Path,
        output_path: Path,
    ) -> None:
        clean_model_name = self._gather_filename(model_folder_path)
        image_location = self.detect_image_location(model_folder_path)
        shutil.copy2(
            image_location,
            output_path / f"{clean_model_name}{image_location.suffix}",
        )
        self._process_unsupported(
            model_folder_path=model_folder_path,
            general_output_location=output_path,
            root_folders_ignore=[self.presupported_files_location],
        )

        present_extensions = self._process_supported(
            model_folder_path=model_folder_path,
            general_output_location=output_path,
            presupported_files_location=self.presupported_files_location,
        )
        if len(present_extensions) == 0:
            logger.warning(f"Did not find presupported files for file {model_folder_path}!")

        else:
            non_supported_file_tree = self.get_file_tree(output_path / "Unsupported" / clean_model_name / "Models")
            n_non_supported_file_tree = len(non_supported_file_tree)
            for extension in present_extensions:
                supported_file_tree = self.get_file_tree(
                    output_path / "Presupported" / clean_model_name / "Models" / self.MODEL_EXTENSIONS_MAP[extension],
                )
                n_supported_file_tree = len(supported_file_tree)

                is_supported_equal_to_non_supported = n_non_supported_file_tree == n_supported_file_tree
                if not is_supported_equal_to_non_supported:
                    logger.warning(
                        f"Found inconsistency in file {model_folder_path}: {n_non_supported_file_tree} in non-supported"
                        f" vs {n_supported_file_tree} in {self.MODEL_EXTENSIONS_MAP[extension]}",
                    )

    @classmethod
    def _process_unsupported(
        cls,
        model_folder_path: Path,
        general_output_location: Path,
        root_folders_ignore: Iterable[str] | None,
    ) -> None:
        if root_folders_ignore is None:
            root_folders_ignore = []

        model_name = cls._gather_filename(model_folder_path)

        output_model_location = general_output_location / "Unsupported" / model_name
        output_model_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        output_model_files_location = output_model_location / "Models"
        output_model_files_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        for file_or_folder in model_folder_path.iterdir():
            if file_or_folder.is_file():
                continue

            folder = file_or_folder
            if folder.name in root_folders_ignore:
                continue

            cls.extract_all_files_of_given_extension(
                folder_path=folder,
                extension=".stl",
                output_path=output_model_files_location / cls.MODEL_EXTENSIONS_MAP[".stl"],
                folders_to_remove=set(cls.MODEL_EXTENSIONS_MAP.values()),
            )

    @classmethod
    def _process_supported(
        cls,
        model_folder_path: Path,
        general_output_location: Path,
        presupported_files_location: str,
    ):
        model_name = cls._gather_filename(model_folder_path)
        output_model_location = general_output_location / "Presupported" / model_name
        output_model_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        output_model_files_location = output_model_location / "Models"
        output_model_files_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        present_extensions = []
        for model_extension, target_location in cls.MODEL_EXTENSIONS_MAP.items():
            extension_present = cls.extract_all_files_of_given_extension(
                folder_path=model_folder_path / presupported_files_location,
                extension=model_extension,
                output_path=output_model_files_location / target_location,
                folders_to_remove=set(cls.MODEL_EXTENSIONS_MAP.values()),
            )
            if extension_present:
                present_extensions.append(model_extension)

        return present_extensions

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
    def detect_image_location(cls, filepath: Path) -> Path:
        logger.debug(f"Detecting images in {filepath}. List of directory: {list(filepath.iterdir())}")
        images_list = [f for f in filepath.iterdir() if f.suffix.lower() in cls.IMAGE_EXTENSIONS and f.is_file()]
        logger.debug(f"Found total {len(images_list)} images in {filepath}: {images_list}")

        if len(images_list) > 1:
            error_message = f"Found more than one image in {filepath}: {images_list}!"
            raise MultipleImagesFoundException(error_message)
        if len(images_list) == 0:
            error_message = f"Failed to find an image in {filepath}!"
            raise ImageNotFoundException(error_message)

        return images_list[0]

    @staticmethod
    def _gather_filename(
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
        try:
            model_id, filename = filepath.name.split("_")
            model_id = int(model_id)
            return f"{model_id}. {filename}"

        except ValueError as e:
            try:
                logger.warning(f"Falling back to '. ' as delimiter to detect filename for {filepath}")
                model_id, filename = filepath.name.split(". ")
                model_id = int(model_id)
                return f"{model_id}. {filename}"
            except ValueError as e:
                raise ModelNameDetectionException from e

    @staticmethod
    def reverse_dict_with_list_values(d: dict) -> dict:
        if d == {}:
            return {}

        result = {}
        for key, value in d.items():
            for item in value:
                if item in result:
                    existing_key = result[item]
                    raise ValueError(
                        f"Value duplication ({item}) detected when trying to reverse dict: {existing_key}, {key}!",
                    )
                result[item] = key

        return result

    @staticmethod
    def prepare_folders(
        output_path: Path,
        details_dict: dict[str, list[str]],
    ) -> None:
        for key in details_dict:
            (output_path / key / "Unsupported").mkdir(exist_ok=True, parents=True)
            (output_path / key / "Presupported").mkdir(exist_ok=True, parents=True)

        (output_path / "Characters" / "Unsupported").mkdir(exist_ok=True, parents=True)
        (output_path / "Characters" / "Presupported").mkdir(exist_ok=True, parents=True)

    @staticmethod
    def normalize_details(
        details_dict: dict[str, list[str]] | None = None,
    ) -> dict[str, list[str]]:
        details_dict_ = deepcopy(details_dict)
        if details_dict_ is None:
            details_dict_ = {}
        if "Characters" in details_dict_:
            logger.warning(f"Removing 'Characters' as redundant, dropped values: {details_dict_['Characters']}")
            del details_dict_["Characters"]

        return details_dict_

    @classmethod
    def _iter_model_folders(cls, root: Path) -> Iterable[Path]:
        for child in root.iterdir():
            if child.is_file():
                logger.debug("Skipping file %s as it is not a folder with model.", child)
                continue
            folder = child
            folder = cls._flatten_same_name(folder)
            yield folder

    @staticmethod
    def _flatten_same_name(model_folder: Path) -> Path:
        model_name = model_folder.name
        while True:
            entries = [folder for folder in model_folder.iterdir() if folder.is_dir()]
            if len(entries) != 1 or entries[0].name != model_name:
                break

            logger.debug(f"Going deeper to {model_folder / model_name}.")
            model_folder = model_folder / model_name

        return model_folder

    @staticmethod
    def get_file_tree(path: Path) -> list[Path]:
        result = []
        for p in path.rglob("*"):
            if p.is_file():
                result.append(p)

        return result
