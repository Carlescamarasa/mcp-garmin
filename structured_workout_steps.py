from typing import Any, Optional

from garminconnect.workout import ConditionType, StepType, TargetType
from round_shorthand_normalizer import normalize_round_shorthand_steps


STEP_NODE_ALIASES = {
    "workout_step": "workout_step",
    "step": "workout_step",
    "executablestepdto": "workout_step",
    "repeat_group": "repeat_group",
    "repeat": "repeat_group",
    "repeatgroupdto": "repeat_group",
}

STEP_TYPE_MAP: dict[str, dict[str, Any]] = {
    "warmup": {"stepTypeId": StepType.WARMUP, "stepTypeKey": "warmup", "displayOrder": 1},
    "cooldown": {"stepTypeId": StepType.COOLDOWN, "stepTypeKey": "cooldown", "displayOrder": 2},
    "interval": {"stepTypeId": StepType.INTERVAL, "stepTypeKey": "interval", "displayOrder": 3},
    "recovery": {"stepTypeId": StepType.RECOVERY, "stepTypeKey": "recovery", "displayOrder": 4},
    "rest": {"stepTypeId": StepType.REST, "stepTypeKey": "rest", "displayOrder": 5},
    "repeat": {"stepTypeId": StepType.REPEAT, "stepTypeKey": "repeat", "displayOrder": 6},
}

STEP_TYPE_ALIASES = {
    "warmup": "warmup",
    "warm_up": "warmup",
    "cooldown": "cooldown",
    "cool_down": "cooldown",
    "interval": "interval",
    "workout_step": "interval",
    "recovery": "recovery",
    "rest": "rest",
}

END_CONDITION_MAP: dict[str, dict[str, Any]] = {
    "time": {
        "conditionTypeId": ConditionType.TIME,
        "conditionTypeKey": "time",
        "displayOrder": 2,
        "displayable": True,
    },
    "iterations": {
        "conditionTypeId": ConditionType.ITERATIONS,
        "conditionTypeKey": "iterations",
        "displayOrder": 2,
        "displayable": True,
    },
    "distance": {
        "conditionTypeId": ConditionType.DISTANCE,
        "conditionTypeKey": "distance",
        "displayOrder": 2,
        "displayable": True,
    },
    "calories": {
        "conditionTypeId": ConditionType.CALORIES,
        "conditionTypeKey": "calories",
        "displayOrder": 2,
        "displayable": True,
    },
    "heart_rate": {
        "conditionTypeId": ConditionType.HEART_RATE,
        "conditionTypeKey": "heart.rate",
        "displayOrder": 2,
        "displayable": True,
    },
    "cadence": {
        "conditionTypeId": ConditionType.CADENCE,
        "conditionTypeKey": "cadence",
        "displayOrder": 2,
        "displayable": True,
    },
    "power": {
        "conditionTypeId": ConditionType.POWER,
        "conditionTypeKey": "power",
        "displayOrder": 2,
        "displayable": True,
    },
    "lap_button": {
        "conditionTypeId": ConditionType.ITERATIONS,
        "conditionTypeKey": "iterations",
        "displayOrder": 7,
        "displayable": True,
    },
}

END_CONDITION_ALIASES = {
    "time": "time",
    "seconds": "time",
    "sec": "time",
    "reps": "iterations",
    "rep": "iterations",
    "iterations": "iterations",
    "distance": "distance",
    "calories": "calories",
    "heart_rate": "heart_rate",
    "heart-rate": "heart_rate",
    "cadence": "cadence",
    "power": "power",
    "lap_button": "lap_button",
    "lap": "lap_button",
    "lapbutton": "lap_button",
    "button": "lap_button",
    "button_press": "lap_button",
    "open": "lap_button",
}

TARGET_TYPE_MAP: dict[str, dict[str, Any]] = {
    "no_target": {
        "workoutTargetTypeId": TargetType.NO_TARGET,
        "workoutTargetTypeKey": "no.target",
        "displayOrder": 1,
    },
    "heart_rate": {
        "workoutTargetTypeId": TargetType.HEART_RATE,
        "workoutTargetTypeKey": "heart.rate",
        "displayOrder": 2,
    },
    "cadence": {
        "workoutTargetTypeId": TargetType.CADENCE,
        "workoutTargetTypeKey": "cadence",
        "displayOrder": 3,
    },
    "speed": {
        "workoutTargetTypeId": TargetType.SPEED,
        "workoutTargetTypeKey": "speed",
        "displayOrder": 4,
    },
    "power": {
        "workoutTargetTypeId": TargetType.POWER,
        "workoutTargetTypeKey": "power",
        "displayOrder": 5,
    },
    "open": {
        "workoutTargetTypeId": TargetType.OPEN,
        "workoutTargetTypeKey": "open",
        "displayOrder": 6,
    },
}

TARGET_TYPE_ALIASES = {
    "no_target": "no_target",
    "no.target": "no_target",
    "none": "no_target",
    "heart_rate": "heart_rate",
    "heart-rate": "heart_rate",
    "cadence": "cadence",
    "speed": "speed",
    "power": "power",
    "open": "open",
}

REPS_TO_SECONDS_FACTOR = 3.0
OPEN_STEP_DEFAULT_SECONDS = 90.0

def _normalize_token(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_alias(
    raw_value: Any,
    aliases: dict[str, str],
    *,
    path: str,
    field_name: str,
    default: Optional[str] = None,
) -> str:
    if raw_value is None:
        if default is not None:
            return default
        raise ValueError(f"{path}.{field_name} is required")

    key = aliases.get(_normalize_token(raw_value))
    if not key:
        allowed = ", ".join(sorted(set(aliases.values())))
        raise ValueError(f"{path}.{field_name} must be one of: {allowed}")
    return key


def _parse_positive_float(raw_value: Any, *, path: str, field_name: str) -> float:
    if raw_value is None:
        raise ValueError(f"{path}.{field_name} must be numeric")
    try:
        value = float(str(raw_value))
    except ValueError as error:
        raise ValueError(f"{path}.{field_name} must be numeric") from error
    if value <= 0:
        raise ValueError(f"{path}.{field_name} must be > 0")
    return value


def _parse_positive_int(raw_value: Any, *, path: str, field_name: str) -> int:
    if raw_value is None:
        raise ValueError(f"{path}.{field_name} is required")
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}.{field_name} must be an integer") from error
    if value <= 0:
        raise ValueError(f"{path}.{field_name} must be >= 1")
    return value


def _resolve_step_order(node: dict[str, Any], fallback_order: int, *, path: str) -> int:
    raw_order = node.get("stepOrder")
    if raw_order is None:
        return fallback_order
    return _parse_positive_int(raw_order, path=path, field_name="stepOrder")


def _build_executable_step(node: dict[str, Any], *, fallback_order: int, path: str) -> dict[str, Any]:
    description_raw = node.get("description")
    if description_raw is None or not str(description_raw).strip():
        raise ValueError(f"{path}.description is required")
    description = str(description_raw).strip()

    duration_key = _resolve_alias(
        node.get("durationType"),
        END_CONDITION_ALIASES,
        path=path,
        field_name="durationType",
    )
    if duration_key == "lap_button":
        duration_value: Optional[float] = None
    else:
        duration_value = _parse_positive_float(node.get("durationValue"), path=path, field_name="durationValue")
    target_key = _resolve_alias(
        node.get("targetType"),
        TARGET_TYPE_ALIASES,
        path=path,
        field_name="targetType",
        default="no_target",
    )

    normalized_description = _normalize_token(description)
    inferred_step_type = "rest" if "descans" in normalized_description or "rest" in normalized_description else "interval"
    step_type_key = _resolve_alias(
        node.get("stepType"),
        STEP_TYPE_ALIASES,
        path=path,
        field_name="stepType",
        default=inferred_step_type,
    )

    return {
        "type": "ExecutableStepDTO",
        "stepOrder": _resolve_step_order(node, fallback_order, path=path),
        "description": description,
        "stepType": dict(STEP_TYPE_MAP[step_type_key]),
        "endCondition": dict(END_CONDITION_MAP[duration_key]),
        "endConditionValue": duration_value,
        "targetType": dict(TARGET_TYPE_MAP[target_key]),
    }


def _is_repeat_step_type(raw_step_type: Any) -> bool:
    if raw_step_type is None:
        return False
    token = _normalize_token(raw_step_type)
    return token in {"repeat", "repeat_group", "repeatgroupdto"}


def _resolve_node_type(node: dict[str, Any], *, path: str) -> str:
    raw_type = node.get("type")
    if raw_type is not None:
        resolved = _resolve_alias(raw_type, STEP_NODE_ALIASES, path=path, field_name="type")
        if resolved == "workout_step" and _is_repeat_step_type(node.get("stepType")):
            return "repeat_group"
        return resolved

    if _is_repeat_step_type(node.get("stepType")):
        return "repeat_group"

    has_iterations = any(node.get(field) is not None for field in ("iterations", "numberOfIterations", "repeatIterations"))
    has_children = isinstance(node.get("steps"), list) or isinstance(node.get("workoutSteps"), list)
    if has_iterations and has_children:
        return "repeat_group"
    return "workout_step"


def _build_repeat_group(node: dict[str, Any], *, fallback_order: int, path: str) -> dict[str, Any]:
    iterations_raw = node.get("iterations", node.get("numberOfIterations", node.get("repeatIterations")))
    iterations = _parse_positive_int(iterations_raw, path=path, field_name="iterations")

    children_raw = node.get("steps", node.get("workoutSteps"))
    if not isinstance(children_raw, list) or not children_raw:
        raise ValueError(f"{path}.steps must be a non-empty list")

    children = _build_structured_steps(children_raw, path=f"{path}.steps")
    return {
        "type": "RepeatGroupDTO",
        "stepOrder": _resolve_step_order(node, fallback_order, path=path),
        "stepType": dict(STEP_TYPE_MAP["repeat"]),
        "numberOfIterations": iterations,
        "workoutSteps": children,
        "endCondition": {
            "conditionTypeId": ConditionType.ITERATIONS,
            "conditionTypeKey": "iterations",
            "displayOrder": 7,
            "displayable": False,
        },
        "endConditionValue": float(iterations),
        "smartRepeat": bool(node.get("smartRepeat", False)),
    }


def _build_structured_steps(raw_steps: list[dict[str, Any]], *, path: str = "steps") -> list[dict[str, Any]]:
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("steps must be a non-empty list")

    payload_steps: list[dict[str, Any]] = []
    for index, raw_node in enumerate(raw_steps, start=1):
        node_path = f"{path}[{index - 1}]"
        if not isinstance(raw_node, dict):
            raise ValueError(f"{node_path} must be an object")

        node_type = _resolve_node_type(raw_node, path=node_path)
        if node_type == "repeat_group":
            payload_steps.append(_build_repeat_group(raw_node, fallback_order=index, path=node_path))
        else:
            payload_steps.append(_build_executable_step(raw_node, fallback_order=index, path=node_path))
    return payload_steps


def _estimate_step_seconds(step: dict[str, Any]) -> float:
    nested = step.get("workoutSteps")
    if isinstance(nested, list):
        per_iteration = sum(_estimate_step_seconds(child) for child in nested if isinstance(child, dict))
        iterations_raw = step.get("numberOfIterations")
        if iterations_raw is None:
            iterations = 1
        else:
            try:
                iterations = int(str(iterations_raw))
            except ValueError:
                iterations = 1
        return per_iteration * max(iterations, 1)

    end_condition = step.get("endCondition")
    condition_key = end_condition.get("conditionTypeKey") if isinstance(end_condition, dict) else None
    end_condition_value = step.get("endConditionValue")

    if condition_key == "time":
        if end_condition_value is None:
            return 0.0
        try:
            value = float(str(end_condition_value))
        except ValueError:
            return 0.0
        return max(value, 0.0)

    if condition_key == "iterations":
        if end_condition_value is None:
            return OPEN_STEP_DEFAULT_SECONDS
        try:
            reps_value = float(str(end_condition_value))
        except ValueError:
            return OPEN_STEP_DEFAULT_SECONDS
        if reps_value <= 0:
            return OPEN_STEP_DEFAULT_SECONDS

        description = str(step.get("description") or "").lower()
        side_multiplier = 2.0 if "/cama" in description or "per cama" in description else 1.0
        return reps_value * side_multiplier * REPS_TO_SECONDS_FACTOR

    return 0.0


def build_structured_steps_payload(
    *,
    name: str,
    description: str,
    sport: dict[str, Any],
    duration_minutes: int,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_steps = normalize_round_shorthand_steps(steps)
    structured_steps = _build_structured_steps(normalized_steps)
    estimated_from_steps = int(round(sum(_estimate_step_seconds(step) for step in structured_steps)))
    fallback_seconds = max(1, duration_minutes) * 60
    estimated_seconds = estimated_from_steps if estimated_from_steps > 0 else fallback_seconds

    sport_entry = {
        "sportTypeId": sport["sportTypeId"],
        "sportTypeKey": sport["sportTypeKey"],
        "displayOrder": sport["displayOrder"],
    }
    return {
        "workoutName": name,
        "description": description,
        "estimatedDurationInSecs": estimated_seconds,
        "sportType": dict(sport_entry),
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": dict(sport_entry),
                "workoutSteps": structured_steps,
            }
        ],
    }
