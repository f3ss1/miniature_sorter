from pathlib import Path
import shutil
import os

from miniature_sorter import logger
from miniature_sorter.constants import PROJECT_ROOT
from miniature_sorter.rar_handler import RarHandler


class CastNPlayConnector:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}

    def __init__(
        self,
        general_output_location: Path,
        rar_handler: RarHandler,
        unsupported_location: str = "STL/",
        presupported_location_stl: str = "Pre-Supported/STL/",
        presupported_location_lys: str = "Pre-Supported/LYS/",
    ):
        self.general_output_location = general_output_location
        self.rar_handler = rar_handler
        self.unsupported_location = unsupported_location
        self.presupported_location_stl = presupported_location_stl
        self.presupported_location_lys = presupported_location_lys

    def process_model_folder(
        self,
        model_folder_path: Path,
    ):
        clean_model_name = self._gather_filename(model_folder_path)
        image_location = self.detect_image_location(model_folder_path)
        shutil.copy2(
            image_location,
            self.general_output_location / f"{clean_model_name}{image_location.suffix}",
        )
        # self._process_unsupported(
        #    model_folder_path=model_folder_path,
        #    rar_handler=self.rar_handler,
        #    model_name=model_name,
        #    unsupported_location=self.unsupported_location,
        # )

        self._process_supported(
            model_folder_path=model_folder_path,
            general_output_location=self.general_output_location,
            presupported_location_stl=self.presupported_location_stl,
            presupported_location_lys=self.presupported_location_lys,
        )

    @classmethod
    def _process_unsupported(
        cls,
        model_folder_path: Path,
        rar_handler: RarHandler,
        model_name: str,
        unsupported_location: str,
        tmpdir: Path,
    ) -> None:
        original_image_location = cls.detect_image_location(model_folder_path)
        new_folder_location = tmpdir / model_name
        os.mkdir(new_folder_location)
        shutil.copy2(original_image_location, new_folder_location / f"{model_name}{original_image_location.suffix}")
        logger.debug(f"Finished moving image: {os.listdir(new_folder_location)}")

        os.mkdir(new_folder_location / "Model")
        shutil.copytree(
            model_folder_path / unsupported_location,
            new_folder_location / "Model",
            dirs_exist_ok=True,
        )
        logger.debug(f"Finished moving unsupported files: {os.listdir(new_folder_location / 'Model')}")
        rar_handler.compress(new_folder_location, PROJECT_ROOT / "result.rar")

    @classmethod
    def _process_supported(
        cls,
        model_folder_path: Path,
        general_output_location: Path,
        presupported_location_stl: str,
        presupported_location_lys: str,
    ):
        model_name = cls._gather_filename(model_folder_path)
        output_model_location = general_output_location / "Presupported" / model_name
        output_model_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        original_image_location = cls.detect_image_location(model_folder_path)
        shutil.copy2(original_image_location, output_model_location / f"{model_name}{original_image_location.suffix}")
        logger.debug(f"Finished moving image: {os.listdir(output_model_location)}")

        output_model_files_location = output_model_location / "Models"
        output_model_files_location.mkdir(exist_ok=True)  # TODO: replace when finished testing

        shutil.copytree(
            model_folder_path / presupported_location_stl,
            output_model_files_location / "STL",
            dirs_exist_ok=True,  # TODO: replace when finished testing
        )
        logger.debug(f"Finished moving presupported STL files: {os.listdir(output_model_files_location / 'STL')}")

        shutil.copytree(
            model_folder_path / presupported_location_lys,
            output_model_files_location / "LYS",
            dirs_exist_ok=True,  # TODO: replace when finished testing
        )
        logger.debug(f"Finished moving presupported LYS files: {os.listdir(output_model_files_location / 'LYS')}")

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
            return f"{model_id}. {filename}"

        except ValueError as e:
            logger.error(f"Failed to gather model name for folder {filepath}:\n{e}")
            raise e
