from datetime import date as dt_date
from typing import Any, Optional

from garminconnect import Garmin


def _parse_iso_date(field_name: str, value: Optional[str]) -> str:
    if not value:
        raise ValueError(f"{field_name} is required (YYYY-MM-DD)")
    try:
        return dt_date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from error


def _bounded(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def query_activities(
    client: Garmin,
    action: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    activity_id: Optional[str] = None,
    limit: int = 20,
) -> dict[str, Any]:
    normalized_action = action.strip().lower()

    if normalized_action == "list":
        start_day = _parse_iso_date("from_date", from_date)
        end_day = _parse_iso_date("to_date", to_date)
        safe_limit = _bounded(limit, 1, 200)
        activities = client.get_activities_by_date(start_day, end_day)
        selected = activities[:safe_limit]
        return {
            "status": "success",
            "action": "list",
            "fromDate": start_day,
            "toDate": end_day,
            "count": len(selected),
            "activities": selected,
            "message": "Llista d'activitats retornada correctament.",
        }

    if normalized_action == "detail":
        if not activity_id:
            raise ValueError("activity_id is required for action=detail")

        activity = client.get_activity(activity_id)
        return {
            "status": "success",
            "action": "detail",
            "activityId": str(activity_id),
            "activity": activity,
            "message": "Detall d'activitat retornat correctament.",
        }

    return {
        "status": "error",
        "error": "Unknown action",
        "action": action,
        "supportedActions": ["list", "detail"],
    }
