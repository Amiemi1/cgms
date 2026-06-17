from fastapi import APIRouter


router = APIRouter()


@router.get(
    "/release/status"
)
def release_status():

    return {

        "release":

            "CGMS v1.10",

        "readiness":

            99,

        "status":

            "candidate",

        "approved":

            False,

        "next":

            [

                "UI",

                "Documentation",

                "Packaging"
            ]
    }