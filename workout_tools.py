from datetime import date as dt_date
from typing import Any, Callable, Optional

from garminconnect import Garmin

import scheduled_workouts_store as workout_store
from workout_payload_utils import (
    SPORT_TYPE_MAP,
    apply_sport_to_payload,
    bounded,
    build_workout_payload,
    normalize_sport_type,
    parse_iso_date,
    sanitize_for_update,
    sanitize_for_upload,
)


def _upsert_index_entry(
    index_file: str,
    *,
    workout_id: str,
    workout_name: str,
    description: str,
    scheduled_date: str,
    sport_type_key: str,
    last_action: str,
) -> dict[str, Any]:
    return workout_store.upsert_workout(
        index_file,
        {
            "workoutId": str(workout_id),
            "workoutName": workout_name,
            "description": description,
            "date": scheduled_date,
            "sportType": sport_type_key,
            "status": "active",
            "lastAction": last_action,
            "source": "garmin_manage_workout",
        },
    )


def manage_workout(
    client: Garmin,
    *,
    action: str,
    workout_id: Optional[str] = None,
    workout_date: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    sport_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: str = "active",
    duration_minutes: int = 45,
    start: int = 0,
    limit: int = 100,
    from_date: Optional[str] = None,
    dry_run: bool = False,
    index_file: str = "scheduled_workouts_index.json",
    schedule_workout_fn: Optional[Callable[[Garmin, str, str], dict[str, Any]]] = None,
    weekly_plan_runner: Optional[Callable[[dt_date, bool], list[dict[str, Any]]]] = None,
) -> dict[str, Any]:
    normalized_action = action.strip().lower()
    if schedule_workout_fn is None:
        raise ValueError("schedule_workout_fn is required")

    if normalized_action == "create":
        target_date = parse_iso_date("date", workout_date)
        if not name or not name.strip():
            raise ValueError("name is required for action=create")
        if not description or not description.strip():
            raise ValueError("description is required for action=create")

        sport_label = normalize_sport_type(sport_type, default="STRENGTH")
        payload = build_workout_payload(name, description, sport_label, duration_minutes)
        upload_response = client.upload_workout(payload)

        workout_id_value = upload_response.get("workoutId")
        if not workout_id_value:
            raise RuntimeError("upload_workout did not return workoutId")

        workout_id_str = str(workout_id_value)
        schedule_response = schedule_workout_fn(client, workout_id_str, target_date)
        payload_sport = payload.get("sportType")
        payload_sport_key = payload_sport.get("sportTypeKey") if isinstance(payload_sport, dict) else None
        stored_sport_key = payload_sport_key or SPORT_TYPE_MAP[sport_label]["sportTypeKey"]

        _upsert_index_entry(
            index_file,
            workout_id=workout_id_str,
            workout_name=name,
            description=description,
            scheduled_date=target_date,
            sport_type_key=stored_sport_key,
            last_action="create",
        )

        return {
            "status": "success",
            "action": "create",
            "workoutId": workout_id_str,
            "workoutName": name,
            "scheduledDate": target_date,
            "sportType": stored_sport_key,
            "message": "Workout creat i programat correctament.",
            "scheduleResponse": schedule_response,
        }

    if normalized_action == "list_scheduled":
        rows = workout_store.list_workouts(
            index_file,
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=bounded(limit, 1, 500),
        )
        items = [
            {
                "workoutId": row.get("workoutId"),
                "workoutName": row.get("workoutName"),
                "description": row.get("description"),
                "date": row.get("date"),
                "sportType": row.get("sportType"),
                "status": row.get("status"),
                "updatedAt": row.get("updatedAt"),
            }
            for row in rows
        ]
        return {
            "status": "success",
            "action": "list_scheduled",
            "source": "local_index",
            "count": len(items),
            "items": items,
            "message": "Sessions retornades des de l'index local del MCP.",
        }

    if normalized_action == "list_library":
        safe_start = max(0, int(start))
        safe_limit = bounded(int(limit), 1, 200)
        workouts_raw = client.get_workouts(start=safe_start, limit=safe_limit)
        workouts: list[dict[str, Any]] = []
        if isinstance(workouts_raw, list):
            workouts = [workout for workout in workouts_raw if isinstance(workout, dict)]
        elif isinstance(workouts_raw, dict):
            embedded = workouts_raw.get("workouts")
            if isinstance(embedded, list):
                workouts = [workout for workout in embedded if isinstance(workout, dict)]

        if sport_type:
            sport_label = normalize_sport_type(sport_type)
            expected_key = SPORT_TYPE_MAP[sport_label]["sportTypeKey"]
            workouts = [
                workout
                for workout in workouts
                if isinstance(workout, dict)
                and ((workout.get("sportType") or {}).get("sportTypeKey") == expected_key)
            ]

        return {
            "status": "success",
            "action": "list_library",
            "count": len(workouts),
            "items": workouts,
            "message": "Workouts de la biblioteca Garmin retornats correctament.",
        }

    if normalized_action == "update":
        if not workout_id:
            raise ValueError("workout_id is required for action=update")

        current = client.get_workout_by_id(workout_id)
        current_name = current.get("workoutName") or "Workout"
        current_description = current.get("description") or ""
        current_sport_key = ((current.get("sportType") or {}).get("sportTypeKey") or "strength_training")
        current_sport_label = normalize_sport_type(current_sport_key, default="STRENGTH")

        index_entry = workout_store.get_workout(index_file, str(workout_id))
        current_date = (index_entry or {}).get("date")
        target_date = parse_iso_date("date", workout_date) if workout_date else current_date

        new_name = name.strip() if name else current_name
        new_description = description if description is not None else current_description
        new_sport_label = normalize_sport_type(sport_type, default=current_sport_label)

        changed_fields: list[str] = []
        if new_name != current_name:
            changed_fields.append("name")
        if new_description != current_description:
            changed_fields.append("description")
        if new_sport_label != current_sport_label:
            changed_fields.append("sport_type")
        if target_date and target_date != current_date:
            changed_fields.append("date")

        if not changed_fields:
            return {
                "status": "success",
                "action": "update",
                "workoutId": str(workout_id),
                "changedFields": [],
                "message": "No hi ha canvis per aplicar.",
            }

        if "date" in changed_fields:
            if not target_date:
                raise ValueError("Cannot change date because no target date was resolved")

            upload_payload = sanitize_for_upload(current)
            upload_payload["workoutName"] = new_name
            upload_payload["description"] = new_description
            apply_sport_to_payload(upload_payload, new_sport_label)

            created = client.upload_workout(upload_payload)
            new_workout_id = created.get("workoutId")
            if not new_workout_id:
                raise RuntimeError("Failed to create replacement workout while updating date")

            new_workout_id_str = str(new_workout_id)
            schedule_response = schedule_workout_fn(client, new_workout_id_str, target_date)
            client.connectapi(f"/workout-service/workout/{workout_id}", method="DELETE")

            workout_store.mark_workout_deleted(index_file, str(workout_id), reason="replaced")
            _upsert_index_entry(
                index_file,
                workout_id=new_workout_id_str,
                workout_name=new_name,
                description=new_description,
                scheduled_date=target_date,
                sport_type_key=SPORT_TYPE_MAP[new_sport_label]["sportTypeKey"],
                last_action="update",
            )

            return {
                "status": "success",
                "action": "update",
                "oldWorkoutId": str(workout_id),
                "newWorkoutId": new_workout_id_str,
                "scheduledDate": target_date,
                "changedFields": changed_fields,
                "message": "Workout actualitzat i reprogramat amb reemplacament intern.",
                "scheduleResponse": schedule_response,
            }

        update_payload = sanitize_for_update(current)
        update_payload["workoutName"] = new_name
        update_payload["description"] = new_description
        apply_sport_to_payload(update_payload, new_sport_label)
        client.connectapi(f"/workout-service/workout/{workout_id}", method="PUT", json=update_payload)

        if current_date:
            _upsert_index_entry(
                index_file,
                workout_id=str(workout_id),
                workout_name=new_name,
                description=new_description,
                scheduled_date=current_date,
                sport_type_key=SPORT_TYPE_MAP[new_sport_label]["sportTypeKey"],
                last_action="update",
            )

        return {
            "status": "success",
            "action": "update",
            "workoutId": str(workout_id),
            "changedFields": changed_fields,
            "scheduledDate": current_date,
            "message": "Workout actualitzat correctament.",
        }

    if normalized_action == "delete":
        if not workout_id:
            raise ValueError("workout_id is required for action=delete")

        client.connectapi(f"/workout-service/workout/{workout_id}", method="DELETE")
        workout_store.mark_workout_deleted(index_file, str(workout_id), reason="delete")
        return {
            "status": "success",
            "action": "delete",
            "workoutId": str(workout_id),
            "message": "Workout eliminat correctament.",
        }

    if normalized_action == "apply_week_plan":
        if weekly_plan_runner is None:
            raise ValueError("weekly_plan_runner is required for action=apply_week_plan")

        ref_date = dt_date.today()
        if from_date:
            ref_date = dt_date.fromisoformat(from_date)

        items = weekly_plan_runner(ref_date, dry_run)
        if not dry_run:
            for item in items:
                if item.get("status") != "success":
                    continue
                workout_id_value = item.get("workoutId")
                if not workout_id_value:
                    continue

                workout_id_str = str(workout_id_value)
                scheduled_date = str(item.get("scheduledDate"))
                detail = client.get_workout_by_id(workout_id_str)
                detail_sport_key = ((detail.get("sportType") or {}).get("sportTypeKey") or "unknown")
                _upsert_index_entry(
                    index_file,
                    workout_id=workout_id_str,
                    workout_name=str(detail.get("workoutName") or item.get("workoutName") or "Workout"),
                    description=str(detail.get("description") or ""),
                    scheduled_date=scheduled_date,
                    sport_type_key=str(detail_sport_key),
                    last_action="apply_week_plan",
                )

        return {
            "status": "success",
            "action": "apply_week_plan",
            "dryRun": dry_run,
            "count": len(items),
            "items": items,
            "message": "Pla setmanal processat correctament.",
        }

    return {
        "status": "error",
        "error": "Unknown action",
        "action": action,
        "supportedActions": [
            "create",
            "list_scheduled",
            "list_library",
            "update",
            "delete",
            "apply_week_plan",
        ],
    }
