import json
from pathlib import Path


STORE_PATH = Path("data/workspaces.json")


def load_workspaces():

    if not STORE_PATH.exists():
        return {}

    return json.loads(
        STORE_PATH.read_text(
            encoding="utf-8"
        )
    )


def save_workspaces(
    workspaces: dict
):

    STORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    STORE_PATH.write_text(
        json.dumps(
            workspaces,
            indent=2
        ),
        encoding="utf-8"
    )

    return True