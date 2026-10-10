from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import FeedbackRequest, UserInput
from app.services.formatting import (
    plan_to_display_text,
    plan_to_json_text,
)
from app.services.gemini_service import (
    GeminiServiceError,
    generate_nutrition_tip_with_flash,
    generate_workout_gemini,
    update_workout_plan,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error": None,
        },
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
)
def generate_workout(
    request: Request,

    username: str = Form(...),

    user_id: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        user_input = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

        existing_user = (
            db.query(User)
            .filter(
                User.user_id
                == user_input.user_id
            )
            .first()
        )

        workout_plan = generate_workout_gemini(
            username=user_input.username,
            age=user_input.age,
            weight=user_input.weight,
            goal=user_input.goal,
            intensity=user_input.intensity,
        )

        nutrition_tip = (
            generate_nutrition_tip_with_flash(
                goal=user_input.goal,
                age=user_input.age,
                weight=user_input.weight,
            )
        )

        if existing_user:

            existing_user.username = (
                user_input.username
            )

            existing_user.age = (
                user_input.age
            )

            existing_user.weight = (
                user_input.weight
            )

            existing_user.goal = (
                user_input.goal
            )

            existing_user.intensity = (
                user_input.intensity
            )

            existing_user.original_plan = (
                plan_to_json_text(
                    workout_plan
                )
            )

            existing_user.updated_plan = None

            existing_user.feedback = None

            existing_user.nutrition_tip = (
                nutrition_tip
            )

            db.commit()

            user = existing_user

        else:

            user = User(
                user_id=user_input.user_id,
                username=user_input.username,
                age=user_input.age,
                weight=user_input.weight,
                goal=user_input.goal,
                intensity=user_input.intensity,
                original_plan=plan_to_json_text(
                    workout_plan
                ),
                nutrition_tip=nutrition_tip,
            )

            db.add(user)

            db.commit()

            db.refresh(user)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": plan_to_display_text(
                    workout_plan
                ),
                "nutrition_tip": nutrition_tip,
                "updated": False,
                "error": None,
            },
        )

    except GeminiServiceError as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc),
            },
            status_code=503,
        )

    except ValueError as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc),
            },
            status_code=400,
        )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
)
def submit_feedback(
    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        feedback_request = FeedbackRequest(
            user_id=user_id,
            feedback=feedback,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    user = (
        db.query(User)
        .filter(
            User.user_id
            == feedback_request.user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    try:

        updated_plan = update_workout_plan(
            original_plan=user.original_plan,
            feedback=feedback_request.feedback,
            username=user.username,
            goal=user.goal,
            intensity=user.intensity,
        )

        user.updated_plan = (
            plan_to_json_text(
                updated_plan
            )
        )

        user.feedback = (
            feedback_request.feedback
        )

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": plan_to_display_text(
                    updated_plan
                ),
                "nutrition_tip": user.nutrition_tip,
                "updated": True,
                "error": None,
            },
        )

    except GeminiServiceError as exc:

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": plan_to_display_text(
                    user.updated_plan
                    or user.original_plan
                ),
                "nutrition_tip": user.nutrition_tip,
                "updated": False,
                "error": str(exc),
            },
            status_code=503,
        )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
)
def view_all_users(
    request: Request,
    admin_key: str = "",
    db: Session = Depends(get_db),
):

    if admin_key != settings.ADMIN_KEY:

        raise HTTPException(
            status_code=403,
            detail="Invalid admin key.",
        )

    users = (
        db.query(User)
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users,
        },
    )


@router.get(
    "/api/health"
)
def health():

    return {
        "status": "ok",
        "application": settings.APP_NAME,
    }


@router.get(
    "/api/users"
)
def api_users(
    admin_key: str = "",
    db: Session = Depends(get_db),
):

    if admin_key != settings.ADMIN_KEY:

        raise HTTPException(
            status_code=403,
            detail="Invalid admin key.",
        )

    users = (
        db.query(User)
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": user.id,
            "user_id": user.user_id,
            "username": user.username,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "has_updated_plan": bool(
                user.updated_plan
            ),
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            ),
        }
        for user in users
    ]


@router.get(
    "/api/users/{user_id}"
)
def api_user(
    user_id: str,
    admin_key: str = "",
    db: Session = Depends(get_db),
):

    if admin_key != settings.ADMIN_KEY:

        raise HTTPException(
            status_code=403,
            detail="Invalid admin key.",
        )

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return {
        "user_id": user.user_id,
        "username": user.username,
        "age": user.age,
        "weight": user.weight,
        "goal": user.goal,
        "intensity": user.intensity,
        "original_plan": user.original_plan,
        "updated_plan": user.updated_plan,
        "nutrition_tip": user.nutrition_tip,
        "feedback": user.feedback,
    }