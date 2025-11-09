from fastapi import FastAPI
from app.api.routes.incidents import router as incidents_router
from app.db.session import engine, Base
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Incidents API", version="1.0.0", lifespan=lifespan)

app.include_router(incidents_router)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
