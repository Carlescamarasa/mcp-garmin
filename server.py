import os
import sys
import logging
from datetime import date
from typing import Any, Optional

# Keep stdio clean during imports (MCP uses stdout for protocol frames).
_original_stdout = sys.stdout
sys.stdout = sys.stderr

from garminconnect import Garmin
from mcp.server.fastmcp import FastMCP

sys.stdout = _original_stdout


logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("garmin_mcp")

mcp = FastMCP("Garmin Connect MCP")


SESSION_FILE = os.getenv("GARMIN_SESSION_PATH", "session.json")
garmin_api: Optional[Garmin] = None


def get_garmin_client() -> Garmin:
    """Inicialitza i retorna el client Garmin amb la sessió persistent."""
    global garmin_api
    if garmin_api is not None:
        return garmin_api

    if not os.path.exists(SESSION_FILE):
        logger.error("No s'ha trobat la sessió: %s", SESSION_FILE)
        raise FileNotFoundError("Falta session.json. Executa login_once.py primer.")

    try:
        client = Garmin()
        client.garth.load(SESSION_FILE)

        if not client.display_name and client.garth.profile:
            client.display_name = client.garth.profile.get("displayName")

        garmin_api = client
        logger.info("Sessió Garmin carregada correctament")
        return client
    except Exception as error:
        logger.error("Error carregant sessió Garmin: %s", error)
        raise RuntimeError(f"No s'ha pogut carregar la sessió Garmin: {error}")


def _ensure_display_name(client: Garmin) -> None:
    if client.display_name:
        return

    if client.garth.profile:
        client.display_name = client.garth.profile.get("displayName")
        return

    profile = client.get_user_profile()
    client.display_name = profile.get("userName")


def _schedule_workout_internal(client: Garmin, workout_id: str, date_str: str) -> dict[str, Any]:
    """Programa un workout existent al calendari Garmin."""
    url = f"/workout-service/schedule/{workout_id}"
    payload = {"date": date_str}
    return client.connectapi(url, method="POST", json=payload)


def _bounded_limit(limit: int) -> int:
    if limit < 1:
        return 1
    if limit > 200:
        return 200
    return limit


# --- Salut ---

@mcp.tool()
def get_daily_health(day: str) -> dict[str, Any]:
    """
    Resum de salut per a `day` (YYYY-MM-DD).
    Retorna: `sleep`, `stress`, `body_battery` i `resting_heart_rate`.
    """
    client = get_garmin_client()
    _ensure_display_name(client)
    return {
        "date": day,
        "sleep": client.get_sleep_data(day),
        "stress": client.get_stress_data(day),
        "body_battery": client.get_body_battery(day),
        "resting_heart_rate": client.get_rhr_day(day),
    }


@mcp.tool()
def get_sleep_data(day: str) -> dict[str, Any]:
    """
    Dades completes del son per a `day` (YYYY-MM-DD).
    Inclou fases, puntuació, hores totals i resum nocturn.
    """
    return get_garmin_client().get_sleep_data(day)


@mcp.tool()
def get_stress_data(day: str) -> dict[str, Any]:
    """
    Sèrie i resum de l'estrés diari per a `day` (YYYY-MM-DD).
    """
    return get_garmin_client().get_stress_data(day)


@mcp.tool()
def get_body_battery(day: str) -> Any:
    """
    Corba de Body Battery i valors clau de recuperació per a `day` (YYYY-MM-DD).
    """
    return get_garmin_client().get_body_battery(day)


@mcp.tool()
def get_body_composition(day: str) -> dict[str, Any]:
    """
    Composició corporal (pes/greix/massa relacionada) per a `day` (YYYY-MM-DD).
    """
    return get_garmin_client().get_body_composition(day, day)


# --- Rendiment ---

@mcp.tool()
def get_training_status(day: str) -> dict[str, Any]:
    """
    Estat d'entrenament de Garmin per a `day` (YYYY-MM-DD).
    Exemple: productive, maintaining, recovery, etc.
    """
    return get_garmin_client().get_training_status(day)


@mcp.tool()
def get_training_readiness(day: str) -> dict[str, Any]:
    """
    Readiness score i factors de preparació per a `day` (YYYY-MM-DD).
    """
    return get_garmin_client().get_training_readiness(day)


@mcp.tool()
def get_endurance_score(day: str) -> dict[str, Any]:
    """
    Endurance score per a `day` (YYYY-MM-DD).
    Usa mode dia únic i fallback compatible segons versió de llibreria.
    """
    client = get_garmin_client()
    try:
        return client.get_endurance_score(day, day)
    except Exception:
        return client.get_endurance_score(day)


@mcp.tool()
def get_hill_score(day: str) -> dict[str, Any]:
    """
    Hill score per a `day` (YYYY-MM-DD).
    Usa mode dia únic i fallback compatible segons versió de llibreria.
    """
    client = get_garmin_client()
    try:
        return client.get_hill_score(day, day)
    except Exception:
        return client.get_hill_score(day)


@mcp.tool()
def get_max_metrics(day: str) -> dict[str, Any]:
    """
    Mètriques de rendiment màxim (p. ex. VO2max i associades) per a `day`.
    """
    return get_garmin_client().get_max_metrics(day)


# --- Activitats ---

@mcp.tool()
def list_activities(from_date: str, to_date: str, limit: int = 20) -> dict[str, Any]:
    """
    Llista activitats entre `from_date` i `to_date` (YYYY-MM-DD).
    Retorna `count` i `activities` (items complets de Garmin), limitat a màxim 200.
    """
    activities = get_garmin_client().get_activities_by_date(from_date, to_date)
    safe_limit = _bounded_limit(limit)
    return {
        "from_date": from_date,
        "to_date": to_date,
        "count": len(activities[:safe_limit]),
        "activities": activities[:safe_limit],
    }


@mcp.tool()
def get_activity_detail(activity_id: str) -> dict[str, Any]:
    """
    Detall complet d'una activitat per `activity_id`.
    Inclou distància, temps, HR, mapes i mètriques agregades.
    """
    return get_garmin_client().get_activity(activity_id)


# --- Perfil i dispositius ---

@mcp.tool()
def get_devices() -> list[dict[str, Any]]:
    """
    Llista dispositius Garmin associats al compte.
    """
    return get_garmin_client().get_devices()


@mcp.tool()
def get_user_profile() -> dict[str, Any]:
    """
    Perfil d'usuari (id, sexe, altura, pes, preferències i dades bàsiques del compte).
    """
    return get_garmin_client().get_user_profile()


@mcp.tool()
def get_personal_records() -> dict[str, Any]:
    """
    Rècords personals reconeguts per Garmin (running/cycling i variants disponibles).
    """
    return get_garmin_client().get_personal_record()


@mcp.tool()
def get_gear(user_profile_id: Optional[str] = None) -> dict[str, Any]:
    """
    Equipament del compte (sabatilles, bici, etc.).
    Si no envies `user_profile_id`, s'obté automàticament del perfil.
    """
    client = get_garmin_client()
    profile_id = user_profile_id

    if not profile_id:
        profile = client.get_user_profile()
        profile_id = profile.get("userProfileId")

    if not profile_id:
        return {"error": "No s'ha pogut obtenir userProfileId."}

    return client.get_gear(profile_id)


@mcp.tool()
def get_workouts() -> Any:
    """
    Llista workouts guardats al compte Garmin.
    Retorna metadades com `workoutId`, nom, esport i dates de creació/actualització.
    """
    return get_garmin_client().get_workouts()


# --- Planificador setmanal ---

@mcp.tool()
def schedule_user_week_plan(from_date: Optional[str] = None, dry_run: bool = False) -> dict[str, Any]:
    """
    Crea i programa el pla setmanal estructurat (Força A/B/C + Running Suau).

    Inputs:
    - `from_date` opcional (YYYY-MM-DD) per calcular la setmana a partir d'eixa data.
    - `dry_run=True` per previsualitzar passos i dates sense crear res a Garmin.

    Output:
    - `items` amb cada sessió, data objectiu i resultat (o estructura prevista en dry-run).
    """
    from create_user_workouts import run_plan

    reference_date = date.today()
    if from_date:
        reference_date = date.fromisoformat(from_date)

    items = run_plan(reference_date=reference_date, dry_run=dry_run)
    return {
        "status": "success",
        "dry_run": dry_run,
        "count": len(items),
        "items": items,
    }


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as error:
        logger.critical("Error fatal al servidor: %s", error)
        sys.exit(1)
