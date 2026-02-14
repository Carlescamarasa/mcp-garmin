import json
import os
import threading
from datetime import date, datetime, timezone
from typing import Any


INDEX_SCHEMA_VERSION = 1
_STORE_LOCK = threading.Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_store() -> dict[str, Any]:
    return {
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "updatedAt": _utc_now_iso(),
        "items": [],
    }


def _read_store_unlocked(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return _default_store()

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return _default_store()

    if not isinstance(data, dict):
        return _default_store()

    items = data.get("items")
    if not isinstance(items, list):
        data["items"] = []

    data.setdefault("schemaVersion", INDEX_SCHEMA_VERSION)
    data.setdefault("updatedAt", _utc_now_iso())
    return data


def _write_store_unlocked(path: str, store: dict[str, Any]) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    payload = dict(store)
    payload["schemaVersion"] = INDEX_SCHEMA_VERSION
    payload["updatedAt"] = _utc_now_iso()

    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2)
    os.replace(temp_path, path)


def load_store(path: str) -> dict[str, Any]:
    with _STORE_LOCK:
        return _read_store_unlocked(path)


def upsert_workout(path: str, entry: dict[str, Any]) -> dict[str, Any]:
    workout_id = str(entry.get("workoutId", "")).strip()
    if not workout_id:
        raise ValueError("workoutId is required")

    with _STORE_LOCK:
        store = _read_store_unlocked(path)
        items = store.get("items", [])
        now_iso = _utc_now_iso()

        existing_index = None
        for index, current in enumerate(items):
            if str(current.get("workoutId", "")) == workout_id:
                existing_index = index
                break

        merged = dict(entry)
        merged["workoutId"] = workout_id
        merged.setdefault("status", "active")
        merged["updatedAt"] = now_iso

        if existing_index is None:
            merged.setdefault("createdAt", now_iso)
            items.append(merged)
        else:
            previous = dict(items[existing_index])
            merged.setdefault("createdAt", previous.get("createdAt", now_iso))
            items[existing_index] = {**previous, **merged}

        store["items"] = items
        _write_store_unlocked(path, store)
        return merged


def mark_workout_deleted(path: str, workout_id: str, reason: str = "deleted") -> dict[str, Any] | None:
    normalized_id = str(workout_id).strip()
    if not normalized_id:
        raise ValueError("workout_id is required")

    with _STORE_LOCK:
        store = _read_store_unlocked(path)
        items = store.get("items", [])
        for index, current in enumerate(items):
            if str(current.get("workoutId", "")) != normalized_id:
                continue

            updated = dict(current)
            updated["status"] = "deleted"
            updated["updatedAt"] = _utc_now_iso()
            updated["lastAction"] = reason
            items[index] = updated
            store["items"] = items
            _write_store_unlocked(path, store)
            return updated

        return None


def list_workouts(
    path: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str = "active",
    limit: int = 200,
) -> list[dict[str, Any]]:
    if limit < 1:
        limit = 1
    if limit > 1000:
        limit = 1000

    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    if start and end and start > end:
        raise ValueError("start_date must be before or equal to end_date")

    normalized_status = status.lower().strip()
    if normalized_status not in {"active", "deleted", "all"}:
        raise ValueError("status must be one of: active, deleted, all")

    with _STORE_LOCK:
        store = _read_store_unlocked(path)
        items = store.get("items", [])

    filtered: list[dict[str, Any]] = []
    for item in items:
        item_status = str(item.get("status", "active")).lower()
        if normalized_status != "all" and item_status != normalized_status:
            continue

        item_date_raw = item.get("date")
        try:
            item_date = date.fromisoformat(str(item_date_raw))
        except Exception:
            continue

        if start and item_date < start:
            continue
        if end and item_date > end:
            continue

        filtered.append(dict(item))

    filtered.sort(key=lambda row: (str(row.get("date", "")), str(row.get("updatedAt", ""))), reverse=False)
    return filtered[:limit]


def get_workout(path: str, workout_id: str) -> dict[str, Any] | None:
    normalized_id = str(workout_id).strip()
    if not normalized_id:
        raise ValueError("workout_id is required")

    with _STORE_LOCK:
        store = _read_store_unlocked(path)
        for item in store.get("items", []):
            if str(item.get("workoutId", "")) == normalized_id:
                return dict(item)
    return None
