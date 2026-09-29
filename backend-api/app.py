"""Entry point of the Nadd API. Run by uvicorn as `app:app`."""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import models  # noqa: F401  (importing it registers the 9 tables on Base, so create_all can see them)
from core.errors import RuleError
from core.limits import ensure_plans
from database import Base, SessionLocal, engine, get_db
from routes.auth import router as auth_router
from routes.owner import router as owner_router
from routes.plans import router as plans_router
from routes.shops import router as shops_router

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the API starts: create missing tables and make sure the plans exist."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_plans(db)
    yield


app = FastAPI(title="Nadd API", lifespan=lifespan)

# Allow the Next.js site (another port = another origin) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in FRONTEND_ORIGIN.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuleError)
def rule_error(request: Request, exc: RuleError):
    """A broken business rule becomes {"detail": "message"} with the rule's status code."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, exc: RequestValidationError):
    """Replace FastAPI's technical 422 list with one sentence the front-end can show."""
    fields = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")})
    detail = "Some values are missing or in the wrong format"
    return JSONResponse(status_code=422, content={"detail": f"{detail}: {', '.join(fields)}." if fields else f"{detail}."})


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(plans_router, prefix="/plans", tags=["public"])
app.include_router(shops_router, prefix="/shops", tags=["public"])
app.include_router(owner_router, prefix="/owner", tags=["shop owner"])


@app.get("/")
def root():
    return {"message": "Nadd API. See /docs for every endpoint."}


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)):
    """Proves the API is running and can reach the database."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return {"status": "ok", "database": "ok"}
