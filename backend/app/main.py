from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import billing, events, experiments, funnel, game, users

app = FastAPI(title="Popdle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list({settings.frontend_base_url, "http://localhost:5173"}),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def no_store_cache_headers(request, call_next):
    """All API responses are dynamic (today's puzzle changes daily, guesses
    change per request) — without this, browsers/CDNs are free to cache a GET
    response and serve it stale indefinitely since we never set Cache-Control."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(users.router)
app.include_router(game.router)
app.include_router(events.router)
app.include_router(experiments.router)
app.include_router(funnel.router)
app.include_router(billing.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
