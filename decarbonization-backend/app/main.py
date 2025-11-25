from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from app.config import settings
from app.auth.jwt_handler import create_access_token
from app.auth.oauth2_scheme import get_current_user
from app.routers import health

app = FastAPI(
    title="Decarbonization Platform API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])

# Auth endpoint for testing
@app.post("/auth/token")
async def login(username: str, password: str):
    """
    Mock login endpoint. In production, validate against user database.
    """
    if username == "demo" and password == "demo":
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@app.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    """Protected endpoint requiring valid JWT token."""
    return {"message": f"Hello {current_user}"}

@app.get("/")
async def root():
    return {"status": "Decarbonization Platform API Running"}
