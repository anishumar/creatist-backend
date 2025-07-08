from __future__ import annotations

import os
import asyncpg

from dotenv import load_dotenv
from fastapi import FastAPI

from src.utils import UserHandler  # type: ignore  # noqa

load_dotenv()
user_handler = UserHandler()

HOST = os.environ["HOST"]
PORT = os.environ["PORT"]


async def startup():
    await user_handler.init()

    # Initialize PostgreSQL connection pool
    app.state.pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=10
    )
    app.state.jwt_secret = os.environ["JWT_SECRET"]


async def shutdown():
    if hasattr(app.state, 'pool'):
        await app.state.pool.close()


app = FastAPI(title="Creatist API Documentation", on_startup=[startup], on_shutdown=[shutdown])

from .routes import *  # noqa
from .routes.ws_chat import router as ws_router

# Include WebSocket router
app.include_router(ws_router)
