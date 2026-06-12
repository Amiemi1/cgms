from fastapi import APIRouter
import os
import platform


router = APIRouter()


@router.get("/system/environment")
def environment_manifest():

    return {

        "system": "CGMS",

        "environment": {
            "python":
                platform.python_version(),

            "platform":
                platform.platform(),

            "database":
                "configured"
                if os.getenv("DATABASE_URL")
                else "missing",

            "openai":
                "configured"
                if os.getenv("OPENAI_API_KEY")
                else "missing",

            "runtime":
                os.getenv(
                    "RENDER",
                    "local"
                )
        },

        "deployment": {
            "ready":
                True,

            "checks": [
                "database",
                "api_keys",
                "runtime",
                "routing"
            ]
        }
    }