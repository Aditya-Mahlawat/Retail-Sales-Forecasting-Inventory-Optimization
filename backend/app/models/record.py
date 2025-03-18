from typing import Optional
from sqlmodel import SQLModel, Field

class Record(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    value: float
    kpi_name: str = "stockout_risk"
