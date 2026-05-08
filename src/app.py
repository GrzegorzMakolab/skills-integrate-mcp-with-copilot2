"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi import Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import json
import secrets
from pathlib import Path

from db import Database

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


class LoginRequest(BaseModel):
    username: str
    password: str


class MembershipResponse(BaseModel):
    memberships: list[dict]


def _load_teachers() -> dict[str, str]:
    teachers_file = current_dir / "teachers.json"
    if not teachers_file.exists():
        return {}

    with open(teachers_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        teacher["username"]: teacher["password"]
        for teacher in data.get("teachers", [])
        if "username" in teacher and "password" in teacher
    }


TEACHER_CREDENTIALS = _load_teachers()
ACTIVE_ADMIN_SESSIONS: dict[str, str] = {}

DB = Database(
    db_path=current_dir / "school.db",
    schema_path=current_dir / "db" / "schema.sql",
    seed_path=current_dir / "db" / "seed.sql",
)
DB.initialize(with_seed=True)


def _require_admin(admin_token: str | None) -> str:
    if not admin_token:
        raise HTTPException(
            status_code=401,
            detail="Only teachers can register or unregister students"
        )

    username = ACTIVE_ADMIN_SESSIONS.get(admin_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired admin session")

    return username


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return DB.list_activities()


@app.post("/auth/login")
def admin_login(payload: LoginRequest):
    expected_password = TEACHER_CREDENTIALS.get(payload.username)
    if expected_password is None or expected_password != payload.password:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    token = secrets.token_urlsafe(24)
    ACTIVE_ADMIN_SESSIONS[token] = payload.username
    return {"token": token, "username": payload.username}


@app.post("/auth/logout")
def admin_logout(admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(admin_token)
    ACTIVE_ADMIN_SESSIONS.pop(admin_token, None)
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
def admin_me(admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    username = _require_admin(admin_token)
    return {"username": username, "role": "teacher"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    admin_token: str | None = Header(default=None, alias="X-Admin-Token")
):
    """Sign up a student for an activity"""
    _require_admin(admin_token)

    try:
        DB.signup_for_activity(activity_name, email)
    except ValueError as error:
        if str(error) == "activity_not_found":
            raise HTTPException(status_code=404, detail="Activity not found") from error
        if str(error) == "already_registered":
            raise HTTPException(status_code=400, detail="Student is already signed up") from error
        if str(error) == "activity_full":
            raise HTTPException(status_code=400, detail="Activity is full") from error
        raise

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    admin_token: str | None = Header(default=None, alias="X-Admin-Token")
):
    """Unregister a student from an activity"""
    _require_admin(admin_token)

    try:
        DB.unregister_from_activity(activity_name, email)
    except ValueError as error:
        if str(error) == "activity_not_found":
            raise HTTPException(status_code=404, detail="Activity not found") from error
        if str(error) == "not_registered":
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity") from error
        raise

    return {"message": f"Unregistered {email} from {activity_name}"}


@app.get("/students/{student_email}/memberships", response_model=MembershipResponse)
def get_student_memberships(student_email: str):
    try:
        memberships = DB.get_student_memberships(student_email)
    except ValueError as error:
        if str(error) == "student_not_found":
            raise HTTPException(status_code=404, detail="Student not found") from error
        raise

    return {"memberships": memberships}


@app.get("/advisors/{advisor_username}/memberships", response_model=MembershipResponse)
def get_advisor_memberships(advisor_username: str):
    try:
        memberships = DB.get_advisor_memberships(advisor_username)
    except ValueError as error:
        if str(error) == "advisor_not_found":
            raise HTTPException(status_code=404, detail="Advisor not found") from error
        raise

    return {"memberships": memberships}
