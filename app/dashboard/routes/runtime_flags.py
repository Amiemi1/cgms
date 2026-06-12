from fastapi import APIRouter


router = APIRouter()


feature_flags = {
    "audit_enabled": True,
    "autonomy_enabled": True,
    "incident_monitoring": True,
    "verbose_runtime": False
}


@router.get("/runtime/flags")
def get_flags():

    return {
        "flags":
            feature_flags
    }


@router.post("/runtime/flags")
def update_flags(
    payload: dict
):

    name = payload.get(
        "flag"
    )

    value = payload.get(
        "value"
    )

    if name in feature_flags:

        feature_flags[name] = bool(
            value
        )

    return {
        "ok": True,
        "flags":
            feature_flags
    }