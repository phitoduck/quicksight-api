"""
Entrypoing for the Rootski API.

To run this API with ``gunicorn``, use the following command:

.. code-block:: bash

    gunicorn rootski.main.main:create_app() --bind 0.0.0.0:3333
"""

from pathlib import Path
from typing import Optional

import uvicorn

from fastapi import FastAPI
from quicksight_api.config.config import Config
from quicksight_api.main.endpoints.first import router as first_router
from quicksight_api.schemas.core import Services
from quicksight_api.services.auth import AuthService
from quicksight_api.services.database import DBService
from quicksight_api.services.database import DBService
from quicksight_api.services.logger import LoggingService
from starlette.middleware.cors import CORSMiddleware


def create_app(
    config: Optional[Config] = None,
) -> FastAPI:

    if not config:
        config = Config()

    app = FastAPI(title="API")
    app.state.config: Config = config
    app.state.services = Services(
        auth=AuthService.from_config(config=config),
        db=DBService.from_config(config=config),
        logger=LoggingService.from_config(config=config),
    )

    # add routes
    app.include_router(first_router, tags=["First"])

    # add authorized CORS origins (add these origins to response headers to
    # enable frontends at these origins to receive requests from this API)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# configure startup behavior: initialize services on startup
def initialize_app(app: FastAPI):
    services: Services = app.state.services

    logging_service: LoggingService = services.logger
    auth_service: AuthService = services.auth
    db_service: DBService = services.db

    # logging should be initialized first since it alters a global logger variable
    logging_service.init()
    # auth_service.init()
    db_service.init()


def create_default_app():
    config = Config()
    return create_app(config=config)


if __name__ == "__main__":
    app = create_app()
    config: Config = app.state.config
    initialize_app(app)
    uvicorn.run(app, host=config.host, port=config.port)
