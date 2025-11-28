from pathlib import Path

from miniature_sorter.artist_connectors.cast_n_play import CastNPlayConnector
from miniature_sorter.constants import PROJECT_ROOT


def main():
    connector = CastNPlayConnector()
    connector.process_release(
        Path("/home/f3ss1/Downloads/Beyond the Grave - November 2025"),
        PROJECT_ROOT / "result",
    )


if __name__ == "__main__":
    main()
