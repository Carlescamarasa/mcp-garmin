import logging
import sys
import os
import json
from datetime import date, timedelta
from typing import Optional, List, Any

from mcp.server.fastmcp import FastMCP
from garminconnect import Garmin

# Imports per a la creació de workouts
try:
    from garminconnect.workout import (
        RunningWorkout, 
        ExecutableStep,
        TargetType, 
        StepType, 
        ConditionType,
        SportType
    )
except ImportError as e:
    # Fallback o gestió d'error
    logging.warning(f"No s'han pogut importar els models de workout: {e}")

# Configuració de logging a stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("garmin_mcp")

# Inicialització del servidor MCP
mcp = FastMCP("Garmin Connect MCP")

# Global variables per a l'API
garmin_api: Optional[Garmin] = None
SESSION_FILE = "session.json"

def get_garmin_client() -> Garmin:
    """Recupera o inicialitza el client de Garmin amb la sessió guardada."""
    global garmin_api
    if garmin_api:
        return garmin_api

    if not os.path.exists(SESSION_FILE):
        logger.error(f"No s'ha trobat el fitxer de sessió: {SESSION_FILE}")
        raise FileNotFoundError("Primer has d'executar 'login_once.py' per autenticar-te.")

    try:
        logger.info("Carregant sessió de Garmin...")
        garmin_api = Garmin()
        garmin_api.garth.load(SESSION_FILE)
        # Populate display_name needed for health and summary endpoints
        if not garmin_api.display_name:
            garmin_api.display_name = garmin_api.get_user_profile().get("userName")
        logger.info(f"Sessió carregada per a l'usuari: {garmin_api.display_name}")
        return garmin_api
    except Exception as e:
        logger.error(f"Error carregant la sessió: {e}")
        raise RuntimeError(f"Error carregant sessió Garmin: {e}. Torna a executar login_once.py.")

# --- Funcions auxiliars d'escriptura ---

def _schedule_workout_internal(client: Garmin, workout_id: str, date_str: str) -> dict:
    """
    Programa un workout existent al calendari.
    Mètode deduit: POST /workout-service/schedule/{workout_id} amb {"date": "YYYY-MM-DD"}
    """
    url = f"/workout-service/schedule/{workout_id}"
    data = {"date": date_str}
    logger.info(f"Programant workout {workout_id} per al dia {date_str} a {url}")
    
    try:
        response = client.connectapi(url, method="POST", json=data)
        return response
    except Exception as e:
        logger.error(f"Error programant workout: {e}")
        raise e

# --- Tools de Salut Diària ---

@mcp.tool()
def get_daily_health(day: str) -> dict:
    """Obté un resum de les estadístiques de salut principals."""
    client = get_garmin_client()
    try:
        return {
            "date": day,
            "sleep": client.get_sleep_data(day),
            "stress": client.get_stress_data(day),
            "body_battery": client.get_body_battery(day),
            "resting_heart_rate": client.get_rhr_day(day)
        }
    except Exception as e:
        logger.error(f"Error a get_daily_health: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_sleep_data(day: str) -> dict:
    return get_garmin_client().get_sleep_data(day)

@mcp.tool()
def get_stress_data(day: str) -> dict:
    return get_garmin_client().get_stress_data(day)

@mcp.tool()
def get_body_battery(day: str) -> dict:
    return get_garmin_client().get_body_battery(day)

@mcp.tool()
def get_body_composition(day: str) -> dict:
    return get_garmin_client().get_body_composition(day, day)

@mcp.tool()
def get_hydration_data(day: str) -> dict:
    return get_garmin_client().get_hydration_data(day)

@mcp.tool()
def get_respiration_data(day: str) -> dict:
    return get_garmin_client().get_respiration_data(day)

@mcp.tool()
def get_spo2_data(day: str) -> dict:
    return get_garmin_client().get_spo2_data(day)

@mcp.tool()
def get_steps_data(day: str) -> dict:
    return get_garmin_client().get_steps_data(day)

@mcp.tool()
def get_floors(day: str) -> dict:
    return get_garmin_client().get_floors(day)

@mcp.tool()
def get_heart_rates(day: str) -> dict:
    return get_garmin_client().get_heart_rates(day)

@mcp.tool()
def get_user_summary(day: str) -> dict:
    return get_garmin_client().get_user_summary(day)

@mcp.tool()
def get_stats_and_body(day: str) -> dict:
    return get_garmin_client().get_stats_and_body(day)


# --- Tools d'Entrenament i Rendiment ---

@mcp.tool()
def get_training_status(day: str) -> dict:
    return get_garmin_client().get_training_status(day)

@mcp.tool()
def get_training_readiness(day: str) -> dict:
    return get_garmin_client().get_training_readiness(day)

@mcp.tool()
def get_endurance_score(day: str) -> dict:
    try:
        return get_garmin_client().get_endurance_score(day, day)
    except:
        return get_garmin_client().get_endurance_score(day) 

@mcp.tool()
def get_hill_score(day: str) -> dict:
    try:
        return get_garmin_client().get_hill_score(day, day)
    except:
        return get_garmin_client().get_hill_score(day)

@mcp.tool()
def get_max_metrics(day: str) -> dict:
    return get_garmin_client().get_max_metrics(day)


# --- Tools d'Activitat ---

@mcp.tool()
def list_activities(from_date: str, to_date: str, limit: int = 20) -> dict:
    client = get_garmin_client()
    try:
        activities = client.get_activities_by_date(from_date, to_date)
        return {"activities": activities[:limit], "count": len(activities[:limit])}
    except Exception as e:
        logger.error(f"Error llistant activitats: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_activity_detail(activity_id: str) -> dict:
    return get_garmin_client().get_activity(activity_id)

@mcp.tool()
def get_activity_splits(activity_id: str) -> dict:
    return get_garmin_client().get_activity_splits(activity_id)

@mcp.tool()
def get_activity_weather(activity_id: str) -> dict:
    return get_garmin_client().get_activity_weather(activity_id)

@mcp.tool()
def get_activity_hr_zones(activity_id: str) -> dict:
    return get_garmin_client().get_activity_hr_in_timezones(activity_id)

@mcp.tool()
def get_activity_power_zones(activity_id: str) -> dict:
    """Obté el temps en zones de potència per a una activitat."""
    return get_garmin_client().get_activity_power_in_timezones(activity_id)

@mcp.tool()
def download_activity_file(activity_id: str, format: str = "ORIGINAL") -> dict:
    """
    Descarrega el fitxer original de l'activitat (normalment ZIP contenint FIT).
    Retorna els bytes codificats en base64 o guarda a disc (per MCP millor retornar path o status).
    Aquí guardarem a disc temporalment i retornarem el path.
    """
    import base64
    client = get_garmin_client()
    try:
        # El mètode download_activity retorna bytes
        data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat[format])
        
        # Guardem localment amb nom segur
        filename = f"activity_{activity_id}.zip"
        with open(filename, "wb") as f:
            f.write(data)
            
        return {
            "status": "success", 
            "filename": filename, 
            "size": len(data),
            "message": "Fitxer descarregat al directori del servidor."
        }
    except Exception as e:
        return {"error": str(e)}


# --- Tools d'Usuari i Dispositius ---

@mcp.tool()
def get_devices() -> dict:
    return get_garmin_client().get_devices()

@mcp.tool()
def get_device_settings(device_id: str) -> dict:
    return get_garmin_client().get_device_settings(device_id)

@mcp.tool()
def get_device_last_used() -> dict:
    return get_garmin_client().get_device_last_used()

@mcp.tool()
def get_user_profile() -> dict:
    return get_garmin_client().get_user_profile()

@mcp.tool()
def get_privacy_settings() -> dict:
    return get_garmin_client().get_userprofile_settings()

@mcp.tool()
def get_personal_records() -> dict:
    return get_garmin_client().get_personal_record()

@mcp.tool()
def get_badges() -> dict:
    return get_garmin_client().get_earned_badges()

@mcp.tool()
def get_gear(user_profile_id: str = None) -> dict:
    client = get_garmin_client()
    if not user_profile_id:
        profile = client.get_user_profile()
        user_profile_id = profile.get("userProfileId")
    
    if user_profile_id:
        return client.get_gear(user_profile_id)
    else:
        return {"error": "No s'ha pogut obtenir userProfileId automàticament."}

@mcp.tool()
def get_workouts() -> list:
    """Obté una llista de tots els workouts de l'usuari."""
    return get_garmin_client().get_workouts()

# --- Tools de Creació d'Entrenaments ---

@mcp.tool()
def create_running_workout(name: str, duration_minutes: int, date_str: str, description: str = "") -> dict:
    """
    Crea un entrenament de carrera simple i el programa al calendari.
    """
    client = get_garmin_client()
    logger.info(f"Creant workout '{name}' ({duration_minutes} min) per al dia {date_str}...")
    
    try:
        duration_seconds = float(duration_minutes * 60)
        
        # Construim el pas del workout manualment o amb helpers
        step = ExecutableStep(
            stepOrder=1,
            stepType={
                "stepTypeId": StepType.INTERVAL, # Usant constant correcta
                "stepTypeKey": "interval", 
                "displayOrder": 3
            },
            description=description or name,
            endCondition={
                "conditionTypeId": ConditionType.TIME,
                "conditionTypeKey": "time",
                 "displayOrder": 2,
                 "displayable": True
            },
            endConditionValue=duration_seconds,
            targetType={
                "workoutTargetTypeId": TargetType.NO_TARGET, 
                "workoutTargetTypeKey": "no.target",
                "displayOrder": 1
            }
        )
        
        # Segment
        segment = {
            "segmentOrder": 1,
            "sportType": {
                "sportTypeId": SportType.RUNNING, 
                "sportTypeKey": "running",
                "displayOrder": 1
            },
            "workoutSteps": [step]
        }

        # Workout
        # RunningWorkout té sportType per defecte, però workoutSegments és obligatori
        workout = RunningWorkout(
            workoutName=name,
            description=description,
            estimatedDurationInSecs=int(duration_seconds),
            workoutSegments=[segment]
        )
        
        # Upload
        workout_json = workout.model_dump(exclude_none=True, mode="json")
        logger.info("Pujant workout a Garmin...")
        response = client.upload_workout(workout_json)
        
        workout_id = response.get("workoutId")
        if not workout_id:
            logger.error(f"No s'ha obtingut workoutId a la resposta: {response}")
            return {"error": "Upload fallit, no workoutId", "response": response}
            
        logger.info(f"Workout creat amb ID: {workout_id}. Programant al calendari...")
        
        # Schedule
        schedule_response = _schedule_workout_internal(client, str(workout_id), date_str)
        
        return {
            "status": "success",
            "workoutId": workout_id,
            "scheduled_date": date_str,
            "schedule_response": schedule_response
        }
        
    except Exception as e:
        logger.error(f"Error creant/programant workout: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("Iniciant servidor Garmin Connect MCP (Reader + Writer)...")
    try:
        get_garmin_client()
        mcp.run()
    except Exception as e:
        logger.critical(f"Error fatal al servidor: {e}")
        sys.exit(1)
