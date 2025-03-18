from pydantic import BaseModel

class RecordIn(BaseModel):
    name: str
    category: str
    value: float

class SimulationRequest(BaseModel):
    rows: int = 200
    seed: int = 42
