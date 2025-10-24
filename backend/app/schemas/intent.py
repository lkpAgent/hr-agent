from pydantic import BaseModel

class IntentRouteRequest(BaseModel):
    query: str

class IntentRouteResponse(BaseModel):
    intent: str
    route: str
    query: str = ""