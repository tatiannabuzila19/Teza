from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import os
import logging
from routes import auth, pages, prediction, dashboard
from db.users import UserRepository
from db.predictions import PredictionRepository
from db.evaluations import EvaluationRepository

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Coffee Stress Evaluator", version="2.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize databases
UserRepository.init_db()
PredictionRepository.init_db()
EvaluationRepository.init_db()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"[VALIDATION ERROR] Path: {request.url.path}")
    logger.error(f"[VALIDATION ERROR] Method: {request.method}")
    logger.error(f"[VALIDATION ERROR] Full errors: {exc.errors()}")
    
    # Extract and log detailed error info
    for error in exc.errors():
        logger.error(f"[VALIDATION ERROR] Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )

# Include routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(prediction.router)
app.include_router(dashboard.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
