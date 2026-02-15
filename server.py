import logging
import os
import sys
from typing import Any, Optional

# MCP utilitza stdout per al protocol; redirigim imports a stderr.
_original_stdout = sys.stdout
sys.stdout = sys.stderr

from garminconnect import Garmin
from mcp.server.fastmcp import FastMCP

sys.stdout = _original_stdout

from activity_tools import query_activities
from health_tools import build_health_report
from workout_tools import manage_workout


logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("garmin_mcp")

mcp = FastMCP("Garmin Connect MCP")


SESSION_FILE = os.getenv("GARMIN_SESSION_PATH", "session.json")
WORKOUT_INDEX_FILE = os.getenv("GARMIN_WORKOUT_INDEX_PATH", "scheduled_workouts_index.json")
garmin_api: Optional[Garmin] = None


def get_garmin_client() -> Garmin:
    """Inicialitza i retorna el client Garmin amb sessio persistent."""
    global garmin_api
    if garmin_api is not None:
        return garmin_api

    if not os.path.exists(SESSION_FILE):
        raise FileNotFoundError(f"No s'ha trobat session file: {SESSION_FILE}")

    client = Garmin()
    client.garth.load(SESSION_FILE)
    if not client.display_name and client.garth.profile:
        client.display_name = client.garth.profile.get("displayName")

    garmin_api = client
    logger.info("Sessio Garmin carregada correctament")
    return client


def _schedule_workout_internal(client: Garmin, workout_id: str, date_str: str) -> dict[str, Any]:
    """Programa un workout existent al calendari Garmin."""
    url = f"/workout-service/schedule/{workout_id}"
    payload = {"date": date_str}
    result = client.connectapi(url, method="POST", json=payload)
    if isinstance(result, dict):
        return result
    return {"result": result}


@mcp.tool()
def garmin_health_report(
    day: str,
    mode: str = "summary",
    sections: Optional[list[str]] = None,
    include_raw: bool = False,
) -> dict[str, Any]:
    """
    Report agregat de salut/rendiment en una unica crida.

    Inputs:
    - `day` (YYYY-MM-DD): data objectiu.
    - `mode`: `summary` (menys crides API) o `full` (maxima cobertura de dades).
    - `sections`: llista opcional de seccions concretes a incloure.
    - `include_raw`: si `true`, retorna payloads complets de Garmin en `sectionsData`.

    Output:
    - `summary` amb camps estables (sleep score, stress, steps, body battery, resting HR, VO2max, training status/readiness...).
    - `availableSections`, `unavailableSections`, `errors` i `sectionsOverview`.
    - `sectionsData` (nomes quan `include_raw=true`) amb la resposta detallada de cada seccio.
    """
    try:
        return build_health_report(
            client=get_garmin_client(),
            day=day,
            mode=mode,
            sections=sections,
            include_raw=include_raw,
        )
    except Exception as error:
        logger.error("Error in garmin_health_report: %s", error)
        return {"status": "error", "action": "garmin_health_report", "error": str(error)}


@mcp.tool()
def garmin_manage_workout(
    action: str,
    workout_id: Optional[str] = None,
    date: Optional[str] = None,
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
    steps: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """
    CRUD granular de sessions i gestio de pla setmanal amb una sola tool.

    Inputs:
    - `action`: `create`, `list_scheduled`, `list_library`, `update`, `delete`, `apply_week_plan`.
    - `workout_id`: necessari en `update` i `delete`.
    - `date`: data (YYYY-MM-DD) per `create` o per reprogramar en `update`.
    - `name`, `description`, `sport_type`, `duration_minutes`: camps de creacio/edicio.
    - `steps`: llista opcional de passos estructurats per `create` i `update` (reps, temps, descansos, repeat groups).
    - `start_date`, `end_date`, `status`, `start`, `limit`: paràmetres de consulta.
    - `from_date`, `dry_run`: controlen l'accio `apply_week_plan`.

    Output:
    - `status`, `action`, `message`.
    - Segons accio: `workoutId`, `oldWorkoutId/newWorkoutId`, `scheduledDate`, `changedFields`, `count`, `items`.
    - `list_scheduled` llig des de l'index local (`scheduled_workouts_index.json`) per tindre CRUD robust per data.
    """
    try:
        from create_user_workouts import run_plan

        return manage_workout(
            client=get_garmin_client(),
            action=action,
            workout_id=workout_id,
            workout_date=date,
            name=name,
            description=description,
            sport_type=sport_type,
            start_date=start_date,
            end_date=end_date,
            status=status,
            duration_minutes=duration_minutes,
            start=start,
            limit=limit,
            from_date=from_date,
            dry_run=dry_run,
            steps=steps,
            index_file=WORKOUT_INDEX_FILE,
            schedule_workout_fn=_schedule_workout_internal,
            weekly_plan_runner=lambda reference_date, is_dry_run: run_plan(
                reference_date=reference_date,
                dry_run=is_dry_run,
            ),
        )
    except Exception as error:
        logger.error("Error in garmin_manage_workout(%s): %s", action, error)
        return {"status": "error", "action": action, "error": str(error)}


@mcp.tool()
def garmin_activity_query(
    action: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    activity_id: Optional[str] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Consulta d'activitats de Garmin amb una sola tool.

    Inputs:
    - `action`: `list` o `detail`.
    - `from_date` i `to_date` (YYYY-MM-DD): requerits per `list`.
    - `activity_id`: requerit per `detail`.
    - `limit`: maxim d'activitats retornades en `list`.

    Output:
    - en `list`: `fromDate`, `toDate`, `count`, `activities`.
    - en `detail`: `activityId`, `activity`.
    - sempre: `status`, `action`, `message` (o `error` si falla).
    """
    try:
        return query_activities(
            client=get_garmin_client(),
            action=action,
            from_date=from_date,
            to_date=to_date,
            activity_id=activity_id,
            limit=limit,
        )
    except Exception as error:
        logger.error("Error in garmin_activity_query(%s): %s", action, error)
        return {"status": "error", "action": action, "error": str(error)}


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as error:
        logger.critical("Error fatal al servidor: %s", error)
        sys.exit(1)
