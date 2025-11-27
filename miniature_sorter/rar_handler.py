import subprocess
from pathlib import Path


class RarHandler:
    def __init__(self):
        pass

    @staticmethod
    def compress(
        folder_path: Path,
        output_path: Path,
    ) -> None:

        if not folder_path.is_dir():
            raise ValueError("source folder does not exist")

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
