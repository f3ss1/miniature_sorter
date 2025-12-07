from pathlib import Path
import shutil
import os

from miniature_sorter import logger


class CastNPlayConnector:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    MODEL_EXTENSIONS_MAP = {
        ".stl": "STL",
        ".lys": "LYS",
        ".chitu": "CHITU",
    }

    def __init__(
        self,
        unsupported_location: str = "STL/",
        presupported_location_stl: str = "Pre-Supported/STL/",
        presupported_location_lys: str = "Pre-Supported/LYS/",
    ):
        self.unsupported_location = unsupported_location
        self.presupported_location_stl = Path(presupported_location_stl)
        self.presupported_location_lys = Path(presupported_location_lys)

    def process_release(
        self,
        release_path: Path,
        output_path: Path,
        details_dict: dict[str, list[str]] | None = None,
    ) -> None:
        if details_dict is None:
            details_dict = {}
        if "Characters" in details_dict:
            logger.warning(f"Removing 'Characters' as redundant, dropped values: {details_dict['Characters']}")
            del details_dict["Characters"]

        reversed_details_dict = self.reverse_dict_with_list_values(details_dict)
        self.prepare_folders(output_path, details_dict)

        for file_or_folder in release_path.iterdir():
            if file_or_folder.is_file():
                logger.debug(f"Skipping file {file_or_folder} as it is not a folder with model.")
                continue

            model_folder = file_or_folder
            model_type = reversed_details_dict.get(model_folder, "Characters")
            self.process_model_folder(model_folder, output_path / model_type)

    def process_throwback(
        self,
        throwback_path: Path,
        output_path: Path,
        details_dict: dict[str, list[str]] | None = None,
    ) -> None:
        if details_dict is None:
            details_dict = {}
        if "Characters" in details_dict:
            logger.warning(f"Removing 'Characters' as redundant, dropped values: {details_dict['Characters']}")
            del details_dict["Characters"]

        reversed_details_dict = self.reverse_dict_with_list_values(details_dict)
        self.prepare_folders(output_path, details_dict)

        for file_or_folder in throwback_path.iterdir():
            if file_or_folder.is_file():
                logger.debug(f"Skipping file {file_or_folder} as it is not a folder with model.")
                continue

            # Find the required depth. Sometimes there is a folder in folder (perhaps in a folder)
            model_folder = file_or_folder
            model_name = model_folder.name
            while len(os.listdir(model_folder)) == 1 and os.listdir(model_folder)[0] == model_name:
                logger.info(f"Going deeper to {model_folder / model_name}.")
                model_folder = model_folder / model_name

            model_type = reversed_details_dict.get(model_folder, "Characters")
            self.process_model_folder(model_folder, output_path / model_type)

    def process_model_folder(
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
            unsupported_location=self.unsupported_location,
        )

        # TODO: can be missing for bases for example
        self._process_supported(
            model_folder_path=model_folder_path,
            general_output_location=output_path,
            presupported_locations={
                "STL": self.presupported_location_stl,
                "LYS": self.presupported_location_lys,
            },
        )

    @classmethod
    def _process_unsupported(
        cls,
        model_folder_path: Path,
        general_output_location: Path,
        unsupported_location: str,
    ) -> None:
        model_name = cls._gather_filename(model_folder_path)

        output_model_location = general_output_location / "Unsupported" / model_name
        output_model_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        original_image_location = cls.detect_image_location(model_folder_path)
        shutil.copy2(original_image_location, output_model_location / f"{model_name}{original_image_location.suffix}")
        logger.debug(f"Finished moving image: {os.listdir(output_model_location)}")

        output_model_files_location = output_model_location / "Models"
        output_model_files_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        shutil.copytree(
            model_folder_path / unsupported_location,
            output_model_files_location,
            dirs_exist_ok=True,  # TODO: replace when finished testing
        )
        logger.debug(f"Finished moving unsupported STL files: {os.listdir(output_model_files_location)}")

    @classmethod
    def _process_supported(
        cls,
        model_folder_path: Path,
        general_output_location: Path,
        presupported_locations: dict[str, Path],
    ):
        model_name = cls._gather_filename(model_folder_path)
        output_model_location = general_output_location / "Presupported" / model_name
        output_model_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        original_image_location = cls.detect_image_location(model_folder_path)
        shutil.copy2(original_image_location, output_model_location / f"{model_name}{original_image_location.suffix}")
        logger.debug(f"Finished moving image: {os.listdir(output_model_location)}")

        output_model_files_location = output_model_location / "Models"
        output_model_files_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        for location in presupported_locations.values():
            if (model_folder_path / location).exists():
                cls.process_separated(model_folder_path, output_model_files_location, presupported_locations)
                break
        else:
            cls.process_mixed(model_folder_path / "Pre-Supported", output_model_files_location)

    @classmethod
    def process_mixed(
        cls,
        folder_path: Path,
        output_path: Path,
    ):
        for model_extension in cls.MODEL_EXTENSIONS_MAP.keys():
            for path in folder_path.rglob(f"*{model_extension}"):
                rel = path.relative_to(folder_path)
                target = output_path / cls.MODEL_EXTENSIONS_MAP[model_extension] / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

    @classmethod
    def process_separated(
        cls,
        folder_path: Path,
        output_path: Path,
        presupported_locations: dict[str, Path],
    ):
        for file_type, location in presupported_locations.items():
            if not (folder_path / location).exists():
                logger.info(f"Failed to find {location} inside {folder_path} folder, skipping it!")
                continue

            shutil.copytree(
                folder_path / location,
                output_path / file_type.upper(),
                dirs_exist_ok=True,  # TODO: replace when finished testing
            )
            logger.debug(
                f"Finished moving presupported .{file_type} files: {os.listdir(output_path / file_type.upper())}",
            )

    @classmethod
    def detect_image_location(cls, filepath: Path) -> Path:
        logger.debug(f"Detecting images in {filepath}. List of directory: {os.listdir(filepath)}")
        images_list = [f for f in filepath.iterdir() if f.suffix.lower() in cls.IMAGE_EXTENSIONS and f.is_file()]
        logger.debug(f"Found total {len(images_list)} images in {filepath}: {images_list}")

        if len(images_list) > 1:
            error_message = f"Found more than one image in {filepath}: {images_list}!"
            logger.error(error_message)
            raise ValueError(error_message)
        if len(images_list) == 0:
            error_message = f"Failed to find an image in {filepath}!"
            logger.error(error_message)
            raise ValueError(error_message)

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
            logger.error(f"Failed to gather model name for folder {filepath}:\n{e}")
            raise e

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
