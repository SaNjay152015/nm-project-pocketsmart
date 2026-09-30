import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field, EmailStr

from passlib.context import CryptContext
from jose import jwt, JWTError

from database import (
    get_connection,
    add_recommendation,
    get_history,
    get_recommendation,
    get_session_data,
    save_session_data,
    save_recommendation,
    remove_saved_recommendation,
    get_saved_recommendations,
)

from gemini_utils import (
    get_budget_recommendation,
    get_home_recommendation,
    get_party_recommendation,
    get_jewelry_recommendation,
    get_jarvis_response,
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv("SECRET_KEY", "PocketSmart-Sanjay-Change-This-Secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
MAX_IMAGE_SIZE = 8 * 1024 * 1024


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="PocketSmart AI",
    description="Smart Budget & Recommendation Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STATIC FILES  (expects static/css/style.css and static/js/script.js)
# =========================================================

STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# =========================================================
# TEMPLATES
# =========================================================

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# =========================================================
# PASSWORD SECURITY
# =========================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =========================================================
# PYDANTIC MODELS
# =========================================================

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class BudgetRequest(BaseModel):
    income: float = Field(ge=0)
    food: float = Field(ge=0)
    transport: float = Field(ge=0)
    shopping: float = Field(ge=0)
    bills: float = Field(ge=0)


class HomeRequest(BaseModel):
    budget: float = Field(gt=0)
    room: str = Field(min_length=1, max_length=100)
    style: str = Field(min_length=1, max_length=100)
    items: str = Field(min_length=1, max_length=2000)
    quantity: str = Field(min_length=1, max_length=1000)


class PartyRequest(BaseModel):
    budget: float = Field(gt=0)
    guests: int = Field(gt=0, le=10000)
    event_type: str = Field(min_length=1, max_length=100)
    venue: str = Field(min_length=1, max_length=100)


class JarvisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)


class SessionDataRequest(BaseModel):
    data: dict


# =========================================================
# AUTH HELPERS
# =========================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, ValueError, TypeError):
        return None


def extract_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization")

    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    return request.cookies.get("access_token")


def require_user(request: Request):
    token = extract_token(request)

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    user_id = get_user_from_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")

    return user_id


# =========================================================
# USER HELPERS
# =========================================================

def get_user_by_id(user_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return dict(row)


def get_user_by_email(email: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email.lower().strip(),),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return dict(row)


# =========================================================
# FRONTEND PAGES
# =========================================================

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request},
    )


@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request},
    )


# =========================================================
# REGISTER
# =========================================================

@app.post("/api/register")
@app.post("/register")
async def register(data: RegisterRequest):
    name = data.name.strip()
    email = data.email.lower().strip()
    password = data.password

    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    if get_user_by_email(email):
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    password_hash = hash_password(password)

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (name, email, password_hash),
        )
        user_id = cursor.lastrowid
        connection.commit()

    except Exception as error:
        connection.rollback()
        print("REGISTER DATABASE ERROR:", error)
        raise HTTPException(status_code=500, detail="Unable to create account.")

    finally:
        connection.close()

    return {
        "success": True,
        "message": "Account created successfully!",
        "user": {"id": user_id, "name": name, "email": email},
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/api/login")
@app.post("/login")
async def login(data: LoginRequest):
    email = data.email.lower().strip()
    user = get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user["id"])

    response = JSONResponse(
        content={
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
            },
        }
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return response


# =========================================================
# LOGOUT
# =========================================================

@app.post("/api/logout")
@app.post("/logout")
async def logout():
    response = JSONResponse(
        content={"success": True, "message": "Logged out successfully."}
    )
    response.delete_cookie("access_token")
    return response


# =========================================================
# TOKEN
# =========================================================

@app.get("/api/token")
@app.get("/token")
async def token_info(request: Request):
    token = extract_token(request)

    if not token:
        return {"authenticated": False, "user": None}

    user_id = get_user_from_token(token)

    if user_id is None:
        return {"authenticated": False, "user": None}

    user = get_user_by_id(user_id)

    if not user:
        return {"authenticated": False, "user": None}

    return {"authenticated": True, "user": user}


# =========================================================
# SESSION INFO
# =========================================================

@app.get("/api/session-info")
@app.get("/session-info")
async def session_info(request: Request):
    user_id = require_user(request)
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return {"authenticated": True, "user": user}


# =========================================================
# SESSION DATA
# =========================================================

@app.get("/api/session-data")
@app.get("/session-data")
async def read_session_data(request: Request):
    user_id = require_user(request)
    data = get_session_data(user_id)
    return {"success": True, "data": data}


@app.post("/api/session-data")
@app.post("/session-data")
async def write_session_data(request: Request, data: SessionDataRequest):
    user_id = require_user(request)
    save_session_data(user_id, data.data)
    return {"success": True, "message": "Session data saved.", "data": data.data}


# =========================================================
# BUDGET RECOMMENDATION
# =========================================================

@app.post("/api/generate-budget")
@app.post("/generate-budget")
async def generate_budget(request: Request, data: BudgetRequest):
    user_id = require_user(request)

    recommendation = get_budget_recommendation(
        income=data.income,
        food=data.food,
        transport=data.transport,
        shopping=data.shopping,
        bills=data.bills,
    )

    input_data = {
        "income": data.income,
        "food": data.food,
        "transport": data.transport,
        "shopping": data.shopping,
        "bills": data.bills,
    }

    recommendation_id = add_recommendation(
        user_id=user_id,
        planner_type="budget",
        input_data=input_data,
        recommendation=recommendation,
    )

    return {
        "success": True,
        "recommendation_id": recommendation_id,
        "planner_type": "budget",
        "recommendation": recommendation,
    }


# =========================================================
# HOME PLANNER
# =========================================================

@app.post("/api/generate-home")
@app.post("/generate-home")
async def generate_home(request: Request, data: HomeRequest):
    user_id = require_user(request)

    recommendation = get_home_recommendation(
        budget=data.budget,
        room=data.room,
        style=data.style,
        items=data.items,
        quantity=data.quantity,
    )

    input_data = {
        "budget": data.budget,
        "room": data.room,
        "style": data.style,
        "items": data.items,
        "quantity": data.quantity,
    }

    recommendation_id = add_recommendation(
        user_id=user_id,
        planner_type="home",
        input_data=input_data,
        recommendation=recommendation,
    )

    return {
        "success": True,
        "recommendation_id": recommendation_id,
        "planner_type": "home",
        "recommendation": recommendation,
    }


# =========================================================
# PARTY PLANNER
# =========================================================

@app.post("/api/generate-party")
@app.post("/generate-party")
async def generate_party(request: Request, data: PartyRequest):
    user_id = require_user(request)

    recommendation = get_party_recommendation(
        budget=data.budget,
        guests=data.guests,
        event_type=data.event_type,
        venue=data.venue,
    )

    input_data = {
        "budget": data.budget,
        "guests": data.guests,
        "event_type": data.event_type,
        "venue": data.venue,
    }

    recommendation_id = add_recommendation(
        user_id=user_id,
        planner_type="party",
        input_data=input_data,
        recommendation=recommendation,
    )

    return {
        "success": True,
        "recommendation_id": recommendation_id,
        "planner_type": "party",
        "recommendation": recommendation,
    }


# =========================================================
# JEWELRY PLANNER  (multipart form — needs python-multipart)
# =========================================================

@app.post("/api/generate-jewelry")
@app.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form(...),
    outfit_image: Optional[UploadFile] = File(default=None),
):
    user_id = require_user(request)

    if budget <= 0:
        raise HTTPException(
            status_code=400,
            detail="Budget must be greater than zero.",
        )

    image_bytes = None
    image_mime_type = "image/jpeg"

    if outfit_image:
        if outfit_image.content_type:
            allowed_types = {
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/jpg",
            }

            if outfit_image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail="Please upload a JPG, PNG or WEBP image.",
                )

            image_mime_type = outfit_image.content_type

        image_bytes = await outfit_image.read()

        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Image must be smaller than 8 MB.",
            )

        if len(image_bytes) == 0:
            image_bytes = None

    recommendation = get_jewelry_recommendation(
        budget=budget,
        occasion=occasion,
        style=style,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type,
    )

    input_data = {
        "budget": budget,
        "occasion": occasion,
        "style": style,
        "image_uploaded": bool(image_bytes),
    }

    recommendation_id = add_recommendation(
        user_id=user_id,
        planner_type="jewelry",
        input_data=input_data,
        recommendation=recommendation,
    )

    return {
        "success": True,
        "recommendation_id": recommendation_id,
        "planner_type": "jewelry",
        "recommendation": recommendation,
    }


# =========================================================
# JARVIS
# =========================================================

@app.post("/api/jarvis")
async def jarvis(request: Request, data: JarvisRequest):
    user_id = require_user(request)
    session_data = get_session_data(user_id)

    response = get_jarvis_response(
        question=data.question,
        session_data=session_data,
    )

    return {"success": True, "response": response}


# =========================================================
# HISTORY
# =========================================================

@app.get("/api/history")
@app.get("/history")
async def history(request: Request):
    user_id = require_user(request)
    records = get_history(user_id, limit=50)
    return {"success": True, "history": records}


# =========================================================
# SINGLE RECOMMENDATION
# =========================================================

@app.get("/api/recommendations-details/{recommendation_id}")
@app.get("/recommendations-details/{recommendation_id}")
async def recommendation_details(recommendation_id: int, request: Request):
    user_id = require_user(request)
    recommendation = get_recommendation(recommendation_id, user_id)

    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    return {"success": True, "recommendation": recommendation}


# =========================================================
# SAVE / UNSAVE RECOMMENDATION
# =========================================================

@app.post("/api/recommendations/{recommendation_id}/save")
async def save_recommendation_endpoint(recommendation_id: int, request: Request):
    user_id = require_user(request)
    recommendation = get_recommendation(recommendation_id, user_id)

    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    save_recommendation(user_id, recommendation_id)

    return {"success": True, "message": "Recommendation saved."}


@app.delete("/api/recommendations/{recommendation_id}/save")
async def remove_saved_recommendation_endpoint(
    recommendation_id: int, request: Request
):
    user_id = require_user(request)
    remove_saved_recommendation(user_id, recommendation_id)

    return {
        "success": True,
        "message": "Recommendation removed from saved plans.",
    }


@app.get("/api/saved-recommendations")
async def saved_recommendations(request: Request):
    user_id = require_user(request)
    records = get_saved_recommendations(user_id)
    return {"success": True, "saved": records}


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "application": "PocketSmart AI",
        "authentication": "enabled",
        "session_storage": "enabled",
        "recommendation_history": "enabled",
        "gemini_recommendation_engine": "enabled",
    }


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
async def startup_event():
    print("")
    print("=" * 55)
    print("          POCKETSMART AI")
    print("=" * 55)
    print("Authentication: enabled")
    print("Session storage: enabled")
    print("Recommendation history: enabled")
    print("Gemini recommendation engine: enabled")
    print("=" * 55)
    print("")


# =========================================================
# RUN DIRECTLY:  python main.py
# =========================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)