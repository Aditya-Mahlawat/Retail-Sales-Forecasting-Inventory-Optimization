from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "Data Science Project API"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

settings = Settings()
