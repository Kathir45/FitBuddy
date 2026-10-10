import json
from typing import Any

from app.config import settings


class GeminiServiceError(Exception):
    """Raised when Gemini cannot generate a valid response."""


def _get_client():
    """
    Import the Gemini SDK lazily.

    This allows the rest of the application to start and be tested
    even if the Gemini dependency/key has not been configured yet.
    """
    try:
        from google import genai
    except ImportError as exc:
        raise GeminiServiceError(
            "Google Gemini SDK is not installed. "
            "Run: pip install google-genai"
        ) from exc

    if not settings.GEMINI_API_KEY:
        raise GeminiServiceError(
            "GEMINI_API_KEY is missing. "
            "Add it to the .env file."
        )

    return genai.Client(
        api_key=settings.GEMINI_API_KEY
    )


def _extract_json(text: str) -> Any:
    """
    Extract JSON from Gemini output.

    Handles:
    - pure JSON
    - ```json ... ```
    - accidental surrounding text
    """

    if not text:
        raise GeminiServiceError(
            "Gemini returned an empty response."
        )

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(
                    cleaned[start:end + 1]
                )
            except json.JSONDecodeError:
                pass

    raise GeminiServiceError(
        "Gemini returned invalid JSON."
    )


def _generate_content(
    model: str,
    prompt: str,
) -> str:

    client = _get_client()

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
    except Exception as exc:
        raise GeminiServiceError(
            f"Gemini API request failed: {exc}"
        ) from exc

    text = getattr(response, "text", None)

    if not text:
        raise GeminiServiceError(
            "Gemini returned no text."
        )

    return text


def generate_workout_gemini(
    username: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> dict:

    prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

Create a safe, practical and personalized 7-day fitness plan.

User information:
Name: {username}
Age: {age}
Weight: {weight} kg
Fitness goal: {goal}
Workout intensity: {intensity}

Requirements:

1. Generate exactly 7 days.
2. Each day must contain:
   - day
   - focus
   - warmup
   - exercises
   - cooldown
   - recovery_note
3. Each exercise must contain:
   - name
   - sets
   - reps_or_duration
   - rest
4. Adapt the plan to the user's goal and intensity.
5. Include appropriate rest/recovery.
6. Do not prescribe medication.
7. Do not make dangerous or extreme recommendations.
8. Clearly mention that this is general fitness guidance.
9. Return ONLY valid JSON.

Expected structure:

{{
  "title": "Personalized 7-Day Fitness Plan",
  "disclaimer": "General fitness guidance only.",
  "days": [
    {{
      "day": "Day 1",
      "focus": "Full Body",
      "warmup": [
        "5 minutes light walking"
      ],
      "exercises": [
        {{
          "name": "Bodyweight Squat",
          "sets": 3,
          "reps_or_duration": "10 reps",
          "rest": "60 seconds"
        }}
      ],
      "cooldown": [
        "5 minutes gentle stretching"
      ],
      "recovery_note": "Hydrate and rest."
    }}
  ]
}}
"""

    raw = _generate_content(
        settings.WORKOUT_MODEL,
        prompt,
    )

    result = _extract_json(raw)

    if not isinstance(result, dict):
        raise GeminiServiceError(
            "Workout response must be a JSON object."
        )

    days = result.get("days")

    if not isinstance(days, list) or len(days) != 7:
        raise GeminiServiceError(
            "Gemini did not return exactly 7 workout days."
        )

    return result


def generate_nutrition_tip_with_flash(
    goal: str,
    age: int,
    weight: float,
) -> str:

    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Give one concise, practical nutrition or recovery tip.

Fitness goal: {goal}
Age: {age}
Weight: {weight} kg

Requirements:
- Maximum 100 words.
- Practical and easy to understand.
- Do not prescribe medication.
- Do not provide extreme dieting advice.
- Mention hydration, balanced nutrition or recovery when relevant.
- Return plain text only.
"""

    return _generate_content(
        settings.TIP_MODEL,
        prompt,
    ).strip()


def update_workout_plan(
    original_plan: str,
    feedback: str,
    username: str,
    goal: str,
    intensity: str,
) -> dict:

    prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

The user already has a workout plan and wants changes.

User:
Name: {username}
Goal: {goal}
Intensity: {intensity}

Original plan:
{original_plan}

User feedback:
{feedback}

Create an updated 7-day workout plan.

Rules:
1. Preserve useful parts of the original plan.
2. Apply the user's feedback wherever reasonably possible.
3. Keep exactly 7 days.
4. Maintain warm-up, exercises, cooldown and recovery notes.
5. Keep exercise details practical.
6. Include appropriate recovery/rest.
7. Do not recommend medication.
8. Do not provide dangerous or extreme instructions.
9. Return ONLY valid JSON.

Use this structure:

{{
  "title": "Updated 7-Day Fitness Plan",
  "disclaimer": "General fitness guidance only.",
  "change_summary": "Short summary of changes.",
  "days": [
    {{
      "day": "Day 1",
      "focus": "Full Body",
      "warmup": [],
      "exercises": [
        {{
          "name": "Exercise",
          "sets": 3,
          "reps_or_duration": "10 reps",
          "rest": "60 seconds"
        }}
      ],
      "cooldown": [],
      "recovery_note": "Recovery guidance."
    }}
  ]
}}
"""

    raw = _generate_content(
        settings.WORKOUT_MODEL,
        prompt,
    )

    result = _extract_json(raw)

    if not isinstance(result, dict):
        raise GeminiServiceError(
            "Updated workout response must be a JSON object."
        )

    days = result.get("days")

    if not isinstance(days, list) or len(days) != 7:
        raise GeminiServiceError(
            "Updated plan does not contain exactly 7 days."
        )

    return result