from pathlib import Path
import functools
import shutil
import tempfile
import os

from miniature_sorter import logger
from miniature_sorter.constants import PROJECT_ROOT
from miniature_sorter.rar_handler import RarHandler

class CastNPlayConnector:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}

    def __init__(
        self,
        year_month: str,
        rar_handler: RarHandler,
        unsupported_location: str = "STL/",
        presupported_location_stl: str = "Pre-Supported/STL/",
        presupported_location_lys: str = "Pre-Supported/LYS/",
    ):
        self.year_month = year_month
        self.rar_handler = rar_handler
        self.unsupported_location = unsupported_location
        self.presupported_location_stl = presupported_location_stl
        self.presupported_location_lys = presupported_location_lys

    @staticmethod
    def with_tempdir(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tmpdir = Path(tempfile.mkdtemp())
            # expose to the wrapped function
            kwargs.setdefault("tmpdir", tmpdir)

            try:
                return func(*args, **kwargs)
            finally:
                # always cleanup, even on exception
                shutil.rmtree(tmpdir, ignore_errors=True)

        return wrapper

    def process_model_folder(
        self,
        model_folder_path: Path,
    ):
        model_name = self._gather_filename(model_folder_path)
        #self._process_unsupported(
        #    model_folder_path=model_folder_path,
        #    rar_handler=self.rar_handler,
        #    model_name=model_name,
        #    unsupported_location=self.unsupported_location,
        #)

        self._process_supported(
            model_folder_path=model_folder_path,
            rar_handler=self.rar_handler,
            model_name=model_name,
            presupported_location_stl=self.presupported_location_stl,
            presupported_location_lys=self.presupported_location_lys,
        )

    @classmethod
    @with_tempdir
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
        shutil.copytree(model_folder_path / unsupported_location, new_folder_location / "Model", dirs_exist_ok=True)
        logger.debug(f"Finished moving unsupported files: {os.listdir(new_folder_location / "Model")}")
        rar_handler.compress(new_folder_location, PROJECT_ROOT / "result.rar")

    @classmethod
    @with_tempdir
    def _process_supported(
        cls,
        model_folder_path: Path,
        rar_handler: RarHandler,
        model_name: str,
        presupported_location_stl: str,
        presupported_location_lys: str,
        tmpdir: Path,
    ):
        new_folder_location = tmpdir / model_name
        os.mkdir(new_folder_location)

        original_image_location = cls.detect_image_location(model_folder_path)
        shutil.copy2(original_image_location, new_folder_location / f"{model_name}{original_image_location.suffix}")
        logger.debug(f"Finished moving image: {os.listdir(new_folder_location)}")

        os.mkdir(new_folder_location / "Model")
        shutil.copytree(model_folder_path / presupported_location_stl, new_folder_location / "Model/STL", dirs_exist_ok=True)
        logger.debug(f"Finished moving presupported STL files: {os.listdir(new_folder_location / "Model/STL")}")

        shutil.copytree(model_folder_path / presupported_location_lys, new_folder_location / "Model/LYS", dirs_exist_ok=True)
        logger.debug(f"Finished moving presupported LYS files: {os.listdir(new_folder_location / "Model/LYS")}")

        rar_handler.compress(new_folder_location, PROJECT_ROOT / "result.rar")



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
