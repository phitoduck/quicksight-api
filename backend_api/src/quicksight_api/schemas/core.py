from pydantic import BaseModel
from quicksight_api.services.auth import AuthService
from quicksight_api.services.database import DBService
from quicksight_api.services.database import DBService
from quicksight_api.services.logger import LoggingService


class Services(BaseModel):
    auth: AuthService
    db: DBService
    logger: LoggingService

    class Config:
        # allow members of Services to have types that are not pydantic schemas
        arbitrary_types_allowed = True
