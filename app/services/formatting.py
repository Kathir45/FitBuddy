import json
from typing import Any


def plan_to_json_text(plan: Any) -> str:
    return json.dumps(
        plan,
        indent=2,
        ensure_ascii=False,
    )


def plan_to_display_text(plan: Any) -> str:
    if isinstance(plan, str):
        return plan

    lines = []

    title = plan.get(
        "title",
        "7-Day Fitness Plan",
    )

    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")

    disclaimer = plan.get("disclaimer")

    if disclaimer:
        lines.append(
            f"Note: {disclaimer}"
        )
        lines.append("")

    change_summary = plan.get(
        "change_summary"
    )

    if change_summary:
        lines.append(
            f"Changes: {change_summary}"
        )
        lines.append("")

    for day in plan.get("days", []):

        lines.append(
            f"{day.get('day', 'Day')}: "
            f"{day.get('focus', 'Workout')}"
        )

        lines.append("-" * 50)

        warmup = day.get("warmup", [])

        if warmup:
            lines.append("Warm-up:")

            for item in warmup:
                lines.append(
                    f"  • {item}"
                )

        lines.append("")

        exercises = day.get(
            "exercises",
            [],
        )

        if exercises:
            lines.append("Exercises:")

            for exercise in exercises:

                name = exercise.get(
                    "name",
                    "Exercise",
                )

                sets = exercise.get(
                    "sets",
                    "-",
                )

                reps = exercise.get(
                    "reps_or_duration",
                    "-",
                )

                rest = exercise.get(
                    "rest",
                    "-",
                )

                lines.append(
                    f"  • {name} — "
                    f"{sets} sets × {reps} "
                    f"(Rest: {rest})"
                )

        lines.append("")

        cooldown = day.get(
            "cooldown",
            [],
        )

        if cooldown:
            lines.append("Cooldown:")

            for item in cooldown:
                lines.append(
                    f"  • {item}"
                )

        recovery = day.get(
            "recovery_note"
        )

        if recovery:
            lines.append(
                f"\nRecovery: {recovery}"
            )

        lines.append("\n")

    return "\n".join(lines)