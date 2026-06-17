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

@router.get(
    "/release/narrative"
)
def release_narrative():

    return {

        "product":

            "CGMS",

        "version":

            "v1.30",

        "message":

            (
                "Enterprise runtime platform "
                "with governance, connectors, "
                "commercial controls, and "
                "operator visibility."
            ),

        "stage":

            "release_candidate"
    }