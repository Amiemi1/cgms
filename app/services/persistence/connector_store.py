import json
from pathlib import Path


STORE_PATH = Path("data/connectors.json")


def load_connectors():

    if not STORE_PATH.exists():
        return {}

    return json.loads(
        STORE_PATH.read_text(
            encoding="utf-8"
        )
    )


def save_connectors(
    connectors: dict
):

    STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    STORE_PATH.write_text(
        json.dumps(
            connectors,
            indent=2
        ),
        encoding="utf-8"
    )

    return True