from fastapi import FastAPI

from app.services.orchestration.bootstrap import bootstrap_event_bus


app = FastAPI(title="CGMS API")


@app.on_event("startup")
def startup_event_bus() -> None:
    """
    Bootstrap CGMS platform services at application startup.
    """

    bootstrap_event_bus()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CGMS API is running"}