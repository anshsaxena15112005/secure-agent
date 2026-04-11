from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.routes import auth, policy, agent, incidents, reports, websocket, events, demo
from backend.security.auth import seed_default_users

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_default_users()
    yield


app = FastAPI(
    title="Secure Agent API",
    description="API for the Secure Agent system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(policy.router, prefix="/api/v1/policy", tags=["Policy"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["Incidents"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["Demo"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "message": "Secure Agent is running"
    }


def serve_page(filename: str) -> FileResponse:
    response = FileResponse(FRONTEND_DIR / filename)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/")
async def home():
    return serve_page("login.html")


@app.get("/login")
async def login_page():
    return serve_page("login.html")


@app.get("/dashboard")
async def dashboard_page():
    return serve_page("dashboard.html")


@app.get("/testing")
async def testing_page():
    return serve_page("testing.html")


@app.get("/incidents")
async def incidents_page():
    return serve_page("incidents.html")


@app.get("/reports")
async def reports_page():
    return serve_page("reports.html")


@app.get("/policy-editor")
async def policy_editor_page():
    return serve_page("policy_editor.html")