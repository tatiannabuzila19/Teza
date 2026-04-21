from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.auth_service import AuthService
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_token_from_request(request: Request) -> str:
    """Extract JWT token from cookies or headers."""
    # Try to get from Authorization header first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    # Try to get from cookies
    token = request.cookies.get("access_token")
    return token

def is_authenticated(request: Request) -> bool:
    """Check if user is authenticated."""
    token = get_token_from_request(request)
    if not token:
        return False
    
    try:
        AuthService.verify_token(token)
        return True
    except:
        return False

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve login page."""
    # If already authenticated, redirect to dashboard
    if is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve dashboard page - requires authentication."""
    if not is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/form", response_class=HTMLResponse)
async def form_page(request: Request):
    """Serve form page - requires authentication."""
    if not is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("form.html", {"request": request})
