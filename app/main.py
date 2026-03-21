from fastapi import FastAPI

app = FastAPI(title="CGMS API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CGMS API is running"}