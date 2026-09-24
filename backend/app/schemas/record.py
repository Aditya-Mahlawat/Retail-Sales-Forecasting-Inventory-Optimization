from pydantic import BaseModel

    mape: float
    name: str
    category: str
    value: float

class SimulationRequest(BaseModel):
    rows: int = 200
    seed: int = 42
