import copy
import unicodedata
from datetime import date as dt_date
from typing import Any, Optional, cast

from garminconnect.workout import (
    ConditionType,
    ExecutableStep,
    FitnessEquipmentWorkout,
    RepeatGroup,
    RunningWorkout,
    StepType,
    TargetType,
    WorkoutSegment,
)
from structured_workout_steps import build_structured_steps_payload


SPORT_TYPE_MAP: dict[str, dict[str, Any]] = {
    "RUNNING": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
    "STRENGTH": {"sportTypeId": 20, "sportTypeKey": "strength_training", "displayOrder": 6},
    "CARDIO": {"sportTypeId": 6, "sportTypeKey": "cardio_training", "displayOrder": 6},
    "HIIT": {"sportTypeId": 33, "sportTypeKey": "hiit", "displayOrder": 6},
}

SPORT_TYPE_ALIASES = {
    "RUNNING": "RUNNING",
    "RUN": "RUNNING",
    "running": "RUNNING",
    "STRENGTH": "STRENGTH",
    "strength": "STRENGTH",
    "strength_training": "STRENGTH",
    "CARDIO": "CARDIO",
    "cardio": "CARDIO",
    "cardio_training": "CARDIO",
    "HIIT": "HIIT",
    "hiit": "HIIT",
}


def bounded(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def parse_iso_date(field_name: str, value: Optional[str]) -> str:
    if not value:
        raise ValueError(f"{field_name} is required (YYYY-MM-DD)")
    try:
        return dt_date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from error


def normalize_sport_type(value: Optional[str], default: str = "STRENGTH") -> str:
    if value is None:
        return default
    normalized = SPORT_TYPE_ALIASES.get(str(value).strip(), "")
    if not normalized:
        allowed = ", ".join(sorted(SPORT_TYPE_MAP.keys()))
        raise ValueError(f"sport_type must be one of: {allowed}")
    return normalized


def sport_payload(sport_label: str) -> dict[str, Any]:
    return dict(SPORT_TYPE_MAP[sport_label])


def _normalize_name_key(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _build_strength_template_payload(name: str, description: str) -> Optional[dict[str, Any]]:
    normalized = _normalize_name_key(name)
    builder_name: Optional[str] = None
    if "forca a" in normalized:
        builder_name = "build_workout_force_a"
    elif "forca b" in normalized:
        builder_name = "build_workout_force_b"
    elif "forca c" in normalized:
        builder_name = "build_workout_force_c"

    if builder_name is None:
        return None

    try:
        import create_user_workouts as templates

        builder = getattr(templates, builder_name, None)
        if not callable(builder):
            return None

        workout: Any = builder()
        setattr(workout, "workoutName", name)
        setattr(workout, "description", description)
        model_dump = getattr(workout, "model_dump", None)
        if not callable(model_dump):
            return None
        payload_obj = model_dump(exclude_none=True, mode="json")
        if not isinstance(payload_obj, dict):
            return None
        payload: dict[str, Any] = dict(payload_obj)

        segment_sport = None
        segments = payload.get("workoutSegments")
        if isinstance(segments, list) and segments and isinstance(segments[0], dict):
            segment_sport = segments[0].get("sportType")
        if isinstance(segment_sport, dict):
            payload["sportType"] = dict(segment_sport)

        # Garmin often stores HIIT custom strength payloads as null sportType.
        # Force cardio_training for compatibility while keeping structured steps.
        top_sport = payload.get("sportType")
        if isinstance(top_sport, dict) and top_sport.get("sportTypeKey") == "hiit":
            cardio = sport_payload("CARDIO")
            payload["sportType"] = dict(cardio)
            if isinstance(segments, list):
                for segment in segments:
                    if isinstance(segment, dict):
                        segment["sportType"] = dict(cardio)

        return payload
    except Exception:
        return None


def _make_time_step(description: str, seconds: int, step_order: int, step_type: int, step_key: str) -> ExecutableStep:
    step = ExecutableStep(
        stepOrder=step_order,
        stepType={"stepTypeId": step_type, "stepTypeKey": step_key, "displayOrder": 1},
        targetType={
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
    )
    setattr(step, "description", description)
    step.endCondition = {
        "conditionTypeId": ConditionType.TIME,
        "conditionTypeKey": "time",
        "displayOrder": 2,
        "displayable": True,
    }
    step.endConditionValue = float(seconds)
    return step


def build_workout_payload(
    name: str,
    description: str,
    sport_label: str,
    duration_minutes: int,
    steps: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    if not name.strip():
        raise ValueError("name is required")
    if not description.strip():
        raise ValueError("description is required")

    if steps is not None:
        return build_structured_steps_payload(
            name=name,
            description=description,
            sport=sport_payload(sport_label),
            duration_minutes=duration_minutes,
            steps=steps,
        )

    if sport_label == "STRENGTH":
        template_payload = _build_strength_template_payload(name, description)
        if template_payload:
            return template_payload

    duration = bounded(duration_minutes, 10, 480)
    total_seconds = duration * 60
    warmup_seconds = 5 * 60
    cooldown_seconds = 5 * 60
    main_seconds = total_seconds - warmup_seconds - cooldown_seconds
    if main_seconds < 60:
        warmup_seconds = 2 * 60
        cooldown_seconds = 2 * 60
        main_seconds = total_seconds - warmup_seconds - cooldown_seconds

    default_steps: list[ExecutableStep | RepeatGroup] = [
        _make_time_step("Escalfament", warmup_seconds, 1, StepType.WARMUP, "warmup"),
        _make_time_step("Bloc principal", main_seconds, 2, StepType.INTERVAL, "interval"),
        _make_time_step("Tornada a la calma", cooldown_seconds, 3, StepType.COOLDOWN, "cooldown"),
    ]

    sport = sport_payload(sport_label)
    segment = WorkoutSegment(
        segmentOrder=1,
        sportType={
            "sportTypeId": sport["sportTypeId"],
            "sportTypeKey": sport["sportTypeKey"],
            "displayOrder": sport["displayOrder"],
        },
        workoutSteps=cast(list[ExecutableStep | RepeatGroup], default_steps),
    )

    if sport_label == "RUNNING":
        workout = RunningWorkout(
            workoutName=name,
            estimatedDurationInSecs=total_seconds,
            workoutSegments=[segment],
        )
    else:
        workout = FitnessEquipmentWorkout(
            workoutName=name,
            estimatedDurationInSecs=total_seconds,
            workoutSegments=[segment],
        )

    setattr(workout, "description", description)
    payload = workout.model_dump(exclude_none=True, mode="json")
    payload["sportType"] = {
        "sportTypeId": sport["sportTypeId"],
        "sportTypeKey": sport["sportTypeKey"],
        "displayOrder": sport["displayOrder"],
    }
    return payload


def sanitize_for_upload(workout_detail: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(workout_detail)
    for key in ("workoutId", "ownerId", "createdDate", "updateDate", "author", "consumer"):
        payload.pop(key, None)
    return payload


def sanitize_for_update(workout_detail: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(workout_detail)
    for key in ("createdDate", "updateDate", "author", "consumer"):
        payload.pop(key, None)
    return payload


def apply_sport_to_payload(payload: dict[str, Any], sport_label: str) -> None:
    sport = sport_payload(sport_label)
    payload["sportType"] = {
        "sportTypeId": sport["sportTypeId"],
        "sportTypeKey": sport["sportTypeKey"],
        "displayOrder": sport["displayOrder"],
    }
    segments = payload.get("workoutSegments")
    if isinstance(segments, list):
        for segment in segments:
            if isinstance(segment, dict):
                segment["sportType"] = {
                    "sportTypeId": sport["sportTypeId"],
                    "sportTypeKey": sport["sportTypeKey"],
                    "displayOrder": sport["displayOrder"],
                }
