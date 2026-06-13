from app.services.connectors.registry import (
    update_connector
)


def activate_connector(
    connector: str
):

    return update_connector(

        connector,

        {

            "enabled": True,

            "status":
                "connected"
        }
    )


def deactivate_connector(
    connector: str
):

    return update_connector(

        connector,

        {

            "enabled": False,

            "status":
                "not_connected"
        }
    )