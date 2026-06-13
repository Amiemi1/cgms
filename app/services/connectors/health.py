from datetime import datetime

from app.services.connectors.registry import (
    get_connectors
)


def connector_health():

    connectors = get_connectors()

    result = {}

    for name, cfg in connectors.items():

        result[name] = {

            "status":
                cfg["status"],

            "healthy":
                cfg["enabled"],

            "lastChecked":
                datetime.utcnow()
                .isoformat(),

            "latencyMs":
                0 if cfg["enabled"] else None
        }

    return result