from miniature_sorter.rar_handler import RarHandler
from miniature_sorter.constants import PROJECT_ROOT


def main():
    general_output_location = PROJECT_ROOT / "rar_result"
    paths = [
        PROJECT_ROOT / "result/Characters/Presupported",
        PROJECT_ROOT / "result/Characters/Unsupported",
    ]
    for path in paths:
        output_path = general_output_location / path.parent.name / path.name
        output_path.mkdir(parents=True, exist_ok=True)
        RarHandler.compress_folders_in_folder(path, output_path)


if __name__ == "__main__":
    main()
