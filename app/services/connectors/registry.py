connector_registry = {

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

    return connector_registry