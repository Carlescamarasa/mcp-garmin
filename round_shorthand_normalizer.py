import re
from typing import Any, Optional


ROUND_PATTERN = re.compile(r"^\s*ronda\s*(\d+)\s*[:\-]\s*(.+)$", re.IGNORECASE)


def _normalize_token(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _extract_round_descriptor(node: dict[str, Any]) -> Optional[tuple[int, str]]:
    description = node.get("description")
    if not isinstance(description, str):
        return None

    match = ROUND_PATTERN.match(description.strip())
    if not match:
        return None

    return int(match.group(1)), match.group(2).strip()


def _normalize_round_text(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_round_rest_step(node: dict[str, Any]) -> bool:
    description = str(node.get("description") or "").strip().lower()
    if "descans" not in description and "rest" not in description:
        return False

    duration_token = _normalize_token(node.get("durationType") or "")
    return duration_token in {"time", "seconds", "sec"}


def _parse_exercise_item(item: str) -> Optional[dict[str, Any]]:
    token = item.strip().strip(".")
    if not token:
        return None

    match = re.match(r"^(\d+)\s*(?:s|sec|secs|seg|segon|segons|\")\s+(.+)$", token, re.IGNORECASE)
    if match:
        seconds = int(match.group(1))
        description = match.group(2).strip()
        return {
            "type": "workout_step",
            "durationType": "time",
            "durationValue": seconds,
            "description": description,
        }

    match = re.match(r"^(\d+)\s*/\s*cama\s+(.+)$", token, re.IGNORECASE)
    if match:
        reps = int(match.group(1))
        description = f"{match.group(2).strip()} (per cama)"
        return {
            "type": "workout_step",
            "durationType": "reps",
            "durationValue": reps,
            "description": description,
        }

    match = re.match(r"^(\d+)(?:\s*-\s*\d+)?\s*reps?\s+(.+)$", token, re.IGNORECASE)
    if match:
        reps = int(match.group(1))
        description = match.group(2).strip()
        return {
            "type": "workout_step",
            "durationType": "reps",
            "durationValue": reps,
            "description": description,
        }

    match = re.match(r"^(.+?)\s*\((\d+)(?:\s*-\s*\d+)?\s*reps?\)\s*$", token, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        reps = int(match.group(2))
        return {
            "type": "workout_step",
            "durationType": "reps",
            "durationValue": reps,
            "description": description,
        }

    match = re.match(r"^(.+?)\s*\((\d+)\s*(?:s|sec|secs|seg|segons?)\)\s*$", token, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        seconds = int(match.group(2))
        return {
            "type": "workout_step",
            "durationType": "time",
            "durationValue": seconds,
            "description": description,
        }

    match = re.match(r"^(\d+)\s+(.+)$", token)
    if match:
        reps = int(match.group(1))
        description = match.group(2).strip()
        return {
            "type": "workout_step",
            "durationType": "reps",
            "durationValue": reps,
            "description": description,
        }

    return None


def _build_children_from_round_text(
    exercises_text: str,
    rest_step: Optional[dict[str, Any]],
) -> Optional[list[dict[str, Any]]]:
    items = [item.strip() for item in re.split(r"[,;]", exercises_text) if item.strip()]
    if not items:
        return None

    children: list[dict[str, Any]] = []
    for item in items:
        child = _parse_exercise_item(item)
        if child is None:
            return None
        children.append(child)

    if rest_step is not None:
        rest_raw = rest_step.get("durationValue")
        if rest_raw is None:
            rest_value = 60.0
        else:
            try:
                rest_value = float(str(rest_raw))
            except ValueError:
                rest_value = 60.0

        if rest_value > 0:
            children.append(
                {
                    "type": "workout_step",
                    "durationType": "time",
                    "durationValue": rest_value,
                    "description": str(rest_step.get("description") or "Descans entre rondes"),
                    "stepType": "rest",
                }
            )

    return children


def normalize_round_shorthand_steps(raw_steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    index = 0
    while index < len(raw_steps):
        node = raw_steps[index]
        descriptor = _extract_round_descriptor(node)
        if descriptor is None:
            normalized.append(node)
            index += 1
            continue

        group_start = index
        expected_round = 1
        round_count = 0
        first_round_text_raw: Optional[str] = None
        first_round_text_normalized: Optional[str] = None
        rest_between_rounds: Optional[dict[str, Any]] = None
        failed = False

        while index < len(raw_steps):
            current = raw_steps[index]
            current_descriptor = _extract_round_descriptor(current)
            if current_descriptor is None:
                break

            round_number, exercises_text = current_descriptor
            if round_number != expected_round:
                failed = True
                break

            normalized_text = _normalize_round_text(exercises_text)
            if first_round_text_raw is None:
                first_round_text_raw = exercises_text
                first_round_text_normalized = normalized_text
            elif normalized_text != first_round_text_normalized:
                failed = True
                break

            round_count += 1
            expected_round += 1
            index += 1

            if index < len(raw_steps) and _is_round_rest_step(raw_steps[index]):
                if rest_between_rounds is None:
                    rest_between_rounds = raw_steps[index]
                index += 1

        if failed or round_count < 2 or first_round_text_raw is None:
            normalized.append(raw_steps[group_start])
            index = group_start + 1
            continue

        children = _build_children_from_round_text(first_round_text_raw, rest_between_rounds)
        if not children:
            normalized.append(raw_steps[group_start])
            index = group_start + 1
            continue

        normalized.append(
            {
                "type": "repeat_group",
                "stepOrder": raw_steps[group_start].get("stepOrder"),
                "iterations": round_count,
                "steps": children,
            }
        )

    return normalized
