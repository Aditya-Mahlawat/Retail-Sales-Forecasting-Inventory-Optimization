from fastapi import FastAPI
from backend.app.api.v1.routes import router
from backend.app.core.database import init_db

app = FastAPI(title="Project API")
app.include_router(router)

@app.on_event("startup")
def on_startup() -> None:
    init_db()
