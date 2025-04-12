from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

from app.api.v1.router import api_router
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint - serves the home page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Login page.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/mobile-login", response_class=HTMLResponse)
async def mobile_login_page(request: Request):
    """
    Mobile login page.
    """
    return templates.TemplateResponse("mobile_login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Registration page.
    """
    return templates.TemplateResponse("register_simple.html", {"request": request})

@app.get("/test-otp", response_class=HTMLResponse)
async def test_otp_page(request: Request):
    """
    OTP testing page.
    """
    return templates.TemplateResponse("test_otp.html", {"request": request})

@app.get("/simple-test", response_class=HTMLResponse)
async def simple_test_page(request: Request):
    """
    Simple OTP testing page.
    """
    return templates.TemplateResponse("simple_test.html", {"request": request})

@app.get("/direct-test", response_class=HTMLResponse)
async def direct_test_page(request: Request):
    """
    Direct API test page.
    """
    return templates.TemplateResponse("direct_test.html", {"request": request})

@app.get("/patient-dashboard", response_class=HTMLResponse)
async def patient_dashboard(request: Request):
    """
    Patient dashboard page.
    """
    return templates.TemplateResponse("patient_dashboard.html", {"request": request})

@app.get("/doctor-dashboard", response_class=HTMLResponse)
async def doctor_dashboard(request: Request):
    """
    Doctor dashboard page.
    """
    return templates.TemplateResponse("doctor_dashboard.html", {"request": request})

@app.get("/simple-dashboard", response_class=HTMLResponse)
async def simple_dashboard(request: Request):
    """
    Simple dashboard page for testing authentication.
    """
    return templates.TemplateResponse("simple_dashboard.html", {"request": request})

@app.get("/test-login", response_class=HTMLResponse)
async def test_login(request: Request):
    """
    Test login page for debugging authentication issues.
    """
    return templates.TemplateResponse("test_login.html", {"request": request})

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
