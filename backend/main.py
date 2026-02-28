from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import api

app = FastAPI(
    title="Secure Agent API",
    description="API for the Secure Agent system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Secure Agent is running"}
