from fastapi import APIRouter


router = APIRouter()


runtime_policy = {

    "maxHealthDrop": 20,

    "allowAutonomy": True,

    "allowRecovery": True,

    "killSwitchAuthority": [
        "admin",
        "operator"
    ],

    "quarantineThreshold":
        "critical"
}


@router.get(
    "/runtime/policy"
)
def get_policy():

    return runtime_policy


@router.post(
    "/runtime/policy"
)
def update_policy(
    payload: dict
):

    runtime_policy.update(
        payload
    )

    return {
        "ok": True,
        "policy":
            runtime_policy
    }