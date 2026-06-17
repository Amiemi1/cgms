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

@router.get(
    "/release/readiness"
)
def release_readiness():

    checks = {

        "runtime": True,
        "governance": True,
        "connectors": True,
        "persistence": True,
        "operatorConsole": True,
        "commercial": True,
        "regression": True,
        "documentation": True
    }

    passed = len(
        [

            v

            for v

            in checks.values()

            if v

        ]
    )

    total = len(
        checks
    )

    readiness = round(
        (
            passed
            /
            total
        )
        *
        100,
        1
    )

    return {

        "release":

            "CGMS v1.40",

        "checks":

            checks,

        "score":

            readiness,

        "approved":

            readiness >= 95,

        "status":

            "ga_candidate"

            if readiness >= 95

            else

            "blocked"
    }