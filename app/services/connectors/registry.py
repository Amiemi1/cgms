from app.services.persistence.connector_store import (
    load_connectors,
    save_connectors
)


DEFAULT_CONNECTORS = {

    "slack": {
        "enabled": False,
        "status": "not_connected"
    },

    "teams": {
        "enabled": False,
        "status": "not_connected"
    },

    "gmail": {
        "enabled": False,
        "status": "not_connected"
    },

    "calendar": {
        "enabled": False,
        "status": "not_connected"
    }
}


connector_registry = {
    **DEFAULT_CONNECTORS,
    **load_connectors()
}


def get_connectors():

    return connector_registry


def update_connector(
    name,
    config
):

    if name in connector_registry:

        connector_registry[
            name
        ].update(
            config
        )

        save_connectors(
            connector_registry
        )

    return connector_registry