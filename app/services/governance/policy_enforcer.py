from app.dashboard.routes.runtime_policy import (
    runtime_policy
)

from app.dashboard.routes.runtime_quarantine import (
    quarantine_state
)


def enforce_runtime_policy(
    runtime_state: dict
):

    violations = []

    if (
        runtime_state.get(
            "healthScore",
            100
        )
        <
        (
            100 -
            runtime_policy[
                "maxHealthDrop"
            ]
        )
    ):

        violations.append(
            "health_threshold"
        )


    if (
        runtime_state.get(
            "autonomy",
            False
        )
        and
        not runtime_policy[
            "allowAutonomy"
        ]
    ):

        violations.append(
            "autonomy_disabled"
        )


    # =====================================
    # GOVERNED QUARANTINE ENFORCEMENT
    # =====================================

    if violations:

        subsystem = runtime_state.get(
            "subsystem",
            "runtime"
        )

        if (
            subsystem
            not in
            quarantine_state["subsystems"]
        ):

            quarantine_state["subsystems"].append(
                subsystem
            )

        quarantine_state["active"] = True
        quarantine_state["reason"] = ",".join(
            violations
        )


    return {

        "allowed":
            len(
                violations
            ) == 0,

        "violations":
            violations,

        "quarantine":
            quarantine_state
    }