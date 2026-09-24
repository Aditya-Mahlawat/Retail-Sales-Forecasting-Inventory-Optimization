from sqlmodel import SQLModel, create_engine, Session
from backend.app.core.config import settings
# Import all models so that SQLModel metadata registers all tables
from backend.app.models.record import Product, DailySale, PurchaseOrder, ForecastRun

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
