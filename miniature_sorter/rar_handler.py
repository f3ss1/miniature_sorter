import subprocess
from pathlib import Path

from tqdm import tqdm

from miniature_sorter import logger


class RarHandler:
    def __init__(self):
        pass

    @classmethod
    def compress_folders_in_folder(
        cls,
        folder_path: Path,
        output_folder_path: Path,
    ) -> None:
        if not folder_path.is_dir():
            raise ValueError("Source folder does not exist!")

        total_processed = 0
        ignored = []
        exceptions = []
        all_entities = list(folder_path.iterdir())
        for entity in tqdm(all_entities):
            if not entity.is_dir():
                ignored.append(entity.name)
                continue

            try:
                cls.compress_single_folder(folder_path / entity, output_folder_path / (entity.name + ".rar"))
                total_processed += 1
            except Exception:
                exceptions.append(entity)

        if total_processed == 0:
            logger.error(f"No processable folders to rar were found in source={folder_path}.")
        else:
            logger.info(f"Finished processing {total_processed} folders, ignored {ignored}.")
            if len(exceptions) > 0:
                logger.error(f"Encountered {len(exceptions)} exceptions for folders {exceptions}.")

    @staticmethod
    def compress_single_folder(
        folder_path: Path,
        output_path: Path,
    ) -> None:

        if not folder_path.is_dir():
            raise ValueError("Source folder does not exist!")

        # remove existing archive if needed
        if output_path.exists():
            output_path.unlink()

        cmd = [
            "rar",
            "a",
            str(output_path),
            folder_path.name,
        ]

        # run inside the parent to avoid absolute paths inside archive
        proc = subprocess.run(
            cmd,
            cwd=folder_path.parent,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
