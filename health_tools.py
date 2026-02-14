from datetime import date as dt_date
from typing import Any, Optional

from garminconnect import Garmin


SUMMARY_DEFAULT_SECTIONS = [
    "stats_and_body",
    "user_summary",
    "sleep",
    "stress",
    "body_battery",
    "resting_heart_rate",
    "max_metrics",
    "training_status",
    "training_readiness",
    "endurance_score",
    "hill_score",
]

FULL_EXTRA_SECTIONS = [
    "steps_data",
    "floors",
    "heart_rates",
    "spo2",
    "respiration",
    "hydration",
    "hrv",
]

VALID_HEALTH_SECTIONS = set(SUMMARY_DEFAULT_SECTIONS + FULL_EXTRA_SECTIONS)


def _parse_iso_date(field_name: str, value: Optional[str]) -> str:
    if not value:
        raise ValueError(f"{field_name} is required (YYYY-MM-DD)")
    try:
        return dt_date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from error


def _first_value(data: Any, keys: list[str]) -> Any:
    wanted = {key.lower() for key in keys}
    queue: list[Any] = [data]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            for key, value in current.items():
                if str(key).lower() in wanted and value not in (None, ""):
                    return value
                if isinstance(value, (dict, list)):
                    queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)
    return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _body_battery_summary(data: Any) -> dict[str, Optional[float]]:
    if not isinstance(data, list):
        return {"start": None, "end": None, "min": None, "max": None}

    values: list[float] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        value = _safe_float(
            item.get("bodyBatteryValue")
            or item.get("value")
            or item.get("bodyBattery")
            or item.get("charged")
        )
        if value is not None:
            values.append(value)

    if not values:
        return {"start": None, "end": None, "min": None, "max": None}

    return {
        "start": values[0],
        "end": values[-1],
        "min": min(values),
        "max": max(values),
    }


def _section_overview(section_data: Any) -> dict[str, Any]:
    if isinstance(section_data, dict):
        return {"type": "object", "keys": list(section_data.keys())[:25]}
    if isinstance(section_data, list):
        sample_keys = []
        if section_data and isinstance(section_data[0], dict):
            sample_keys = list(section_data[0].keys())[:25]
        return {"type": "array", "count": len(section_data), "sampleKeys": sample_keys}
    return {"type": type(section_data).__name__, "value": section_data}


def _execute_health_call(fetcher: Any) -> tuple[Any, Optional[str]]:
    try:
        return fetcher(), None
    except Exception as error:
        return None, str(error)


def build_health_report(
    client: Garmin,
    day: str,
    mode: str = "summary",
    sections: Optional[list[str]] = None,
    include_raw: bool = False,
) -> dict[str, Any]:
    target_day = _parse_iso_date("day", day)
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"summary", "full"}:
        return {"status": "error", "error": "mode must be 'summary' or 'full'"}

    requested_sections = SUMMARY_DEFAULT_SECTIONS.copy()
    if normalized_mode == "full":
        requested_sections.extend(FULL_EXTRA_SECTIONS)

    if sections:
        custom_sections = []
        unknown = []
        for section in sections:
            candidate = str(section).strip().lower()
            if candidate in VALID_HEALTH_SECTIONS:
                custom_sections.append(candidate)
            else:
                unknown.append(section)
        if unknown:
            return {
                "status": "error",
                "error": "Unknown sections requested",
                "unknownSections": unknown,
                "validSections": sorted(VALID_HEALTH_SECTIONS),
            }
        requested_sections = custom_sections

    section_fetchers: dict[str, Any] = {
        "stats_and_body": lambda: client.get_stats_and_body(target_day),
        "user_summary": lambda: client.get_user_summary(target_day),
        "sleep": lambda: client.get_sleep_data(target_day),
        "stress": lambda: client.get_stress_data(target_day),
        "body_battery": lambda: client.get_body_battery(target_day, target_day),
        "resting_heart_rate": lambda: client.get_rhr_day(target_day),
        "max_metrics": lambda: client.get_max_metrics(target_day),
        "training_status": lambda: client.get_training_status(target_day),
        "training_readiness": lambda: client.get_training_readiness(target_day),
        "endurance_score": lambda: client.get_endurance_score(target_day, target_day),
        "hill_score": lambda: client.get_hill_score(target_day, target_day),
        "steps_data": lambda: client.get_steps_data(target_day),
        "floors": lambda: client.get_floors(target_day),
        "heart_rates": lambda: client.get_heart_rates(target_day),
        "spo2": lambda: client.get_spo2_data(target_day),
        "respiration": lambda: client.get_respiration_data(target_day),
        "hydration": lambda: client.get_hydration_data(target_day),
        "hrv": lambda: client.get_hrv_data(target_day),
    }

    sections_data: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    for section in requested_sections:
        if section not in section_fetchers:
            continue
        value, error = _execute_health_call(section_fetchers[section])
        sections_data[section] = value
        if error:
            errors.append({"section": section, "error": error})

    body_battery = _body_battery_summary(sections_data.get("body_battery"))
    summary = {
        "sleep_score": _safe_float(_first_value(sections_data.get("sleep"), ["overallScore", "sleepScore", "score"])),
        "sleep_total_seconds": _safe_float(
            _first_value(sections_data.get("sleep"), ["sleepTimeSeconds", "totalSleepSeconds", "sleepDuration"])
        ),
        "stress_average": _safe_float(_first_value(sections_data.get("stress"), ["avgStressLevel", "averageStressLevel", "stressAvg"])),
        "stress_max": _safe_float(_first_value(sections_data.get("stress"), ["maxStressLevel", "stressMax"])),
        "steps_total": _safe_float(
            _first_value(sections_data.get("user_summary"), ["totalSteps", "steps", "stepsCount"])
            or _first_value(sections_data.get("stats_and_body"), ["totalSteps", "steps", "stepsCount"])
        ),
        "steps_goal": _safe_float(_first_value(sections_data.get("user_summary"), ["dailyStepGoal", "stepsGoal"])),
        "floors_climbed": _safe_float(_first_value(sections_data.get("floors"), ["climbed", "totalFloorsClimbed", "floorsClimbed"])),
        "body_battery_start": body_battery["start"],
        "body_battery_end": body_battery["end"],
        "body_battery_min": body_battery["min"],
        "body_battery_max": body_battery["max"],
        "resting_heart_rate": _safe_float(_first_value(sections_data.get("resting_heart_rate"), ["value", "restingHeartRate", "rhr"])),
        "vo2max": _safe_float(_first_value(sections_data.get("max_metrics"), ["vo2Max", "vo2max", "maxVO2"])),
        "training_status": _first_value(sections_data.get("training_status"), ["trainingStatus", "status", "overallStatus"]),
        "training_readiness": _safe_float(
            _first_value(sections_data.get("training_readiness"), ["overallScore", "score", "readinessScore"])
        ),
        "endurance_score": _safe_float(_first_value(sections_data.get("endurance_score"), ["score", "enduranceScore"])),
        "hill_score": _safe_float(_first_value(sections_data.get("hill_score"), ["score", "hillScore"])),
        "spo2_average": _safe_float(_first_value(sections_data.get("spo2"), ["averageSpO2", "avgSpo2", "spo2Avg"])),
        "respiration_average": _safe_float(
            _first_value(sections_data.get("respiration"), ["avgRespirationValue", "averageRespiration", "respirationAvg"])
        ),
        "hydration_ml": _safe_float(_first_value(sections_data.get("hydration"), ["valueInML", "consumedMilliliters", "totalHydration"])),
    }

    available_sections = [name for name, value in sections_data.items() if value is not None]
    unavailable_sections = [name for name, value in sections_data.items() if value is None]

    response: dict[str, Any] = {
        "status": "success",
        "date": target_day,
        "mode": normalized_mode,
        "requestedSections": requested_sections,
        "availableSections": available_sections,
        "unavailableSections": unavailable_sections,
        "summary": summary,
        "sectionsOverview": {name: _section_overview(value) for name, value in sections_data.items()},
        "errors": errors,
    }
    if include_raw:
        response["sectionsData"] = sections_data
    return response
