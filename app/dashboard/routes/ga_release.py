from fastapi import APIRouter


router = APIRouter()


@router.get(
    "/release/ga"
)
def ga():

    return {

        "product":

            "CGMS",

        "version":

            "v1.40",

        "state":

            "general_availability",

        "approved":

            True
    }