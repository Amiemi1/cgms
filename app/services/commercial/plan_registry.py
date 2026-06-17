PLANS = {

    "community": {

        "maxWorkspaces": 1,

        "maxEvents": 100
    },

    "team": {

        "maxWorkspaces": 10,

        "maxEvents": 10000
    },

    "enterprise": {

        "maxWorkspaces": 999,

        "maxEvents": 999999
    }
}


ACTIVE_PLAN = {
    "name": "enterprise"
}


def get_active_plan():

    plan = ACTIVE_PLAN[
        "name"
    ]

    return {

        "plan":
            plan,

        "limits":
            PLANS[
                plan
            ]
    }


def set_plan(
    plan
):

    if plan in PLANS:

        ACTIVE_PLAN[
            "name"
        ] = plan

    return get_active_plan()

from app.services.workspace.registry import (
    get_workspaces
)

from app.services.connectors.event_ingestion import (
    INGESTED_EVENTS
)


def enforce_plan_limits():

    active = get_active_plan()

    limits = active[
        "limits"
    ]

    workspaces = get_workspaces()

    total_events = len(
        INGESTED_EVENTS
    )

    violations = []

    if (
        len(workspaces)
        >
        limits[
            "maxWorkspaces"
        ]
    ):

        violations.append(
            "workspace_limit_exceeded"
        )

    if (
        total_events
        >
        limits[
            "maxEvents"
        ]
    ):

        violations.append(
            "event_limit_exceeded"
        )

    return {

        "plan":
            active[
                "plan"
            ],

        "allowed":
            len(
                violations
            ) == 0,

        "violations":
            violations,

        "usage": {

            "workspaces":
                len(workspaces),

            "events":
                total_events
        },

        "limits":
            limits
    }