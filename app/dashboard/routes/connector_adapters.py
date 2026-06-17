from fastapi import APIRouter

from app.services.connectors.slack_adapter import (
    process_slack_event
)

from app.services.connectors.teams_adapter import (
    process_teams_event
)

from app.services.connectors.gmail_adapter import (
    process_gmail_event
)

from app.services.connectors.calendar_adapter import (
    process_calendar_event
)


router = APIRouter()


@router.post("/adapters/slack")
def slack_adapter(
    payload: dict
):

    return process_slack_event(
        payload
    )


@router.post("/adapters/teams")
def teams_adapter(
    payload: dict
):

    return process_teams_event(
        payload
    )


@router.post("/adapters/gmail")
def gmail_adapter(
    payload: dict
):

    return process_gmail_event(
        payload
    )


@router.post("/adapters/calendar")
def calendar_adapter(
    payload: dict
):

    return process_calendar_event(
        payload
    )