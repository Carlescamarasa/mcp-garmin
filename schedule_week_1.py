import logging
import sys
from datetime import date
from garminconnect.workout import (
    RunningWorkout,
    WalkingWorkout,
    FitnessEquipmentWorkout,
    ExecutableStep,
    RepeatGroup,
    StepType,
    ConditionType,
    TargetType,
    SportType,
    WorkoutSegment
)
from server import get_garmin_client, _schedule_workout_internal

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger("schedule_week_1")

def create_and_schedule(client, workout, day_str):
    try:
        logger.info(f"Pujant workout: {workout.workoutName}...")
        payload = workout.model_dump(exclude_none=True, mode="json")
        response = client.upload_workout(payload)
        
        workout_id = response.get("workoutId")
        if not workout_id:
            logger.error(f"Error pujant workout: {response}")
            return
            
        logger.info(f"Programant workout {workout_id} per al {day_str}...")
        _schedule_workout_internal(client, str(workout_id), day_str)
        logger.info("Fet!")
    except Exception as e:
        logger.error(f"Error processant {workout.workoutName}: {e}")

def create_strength_step(description, order, duration=None):
    """
    Helper per crear un pas de força.
    """
    step = ExecutableStep(
        stepOrder=order,
        stepType={"stepTypeId": StepType.INTERVAL, "stepTypeKey": "interval", "displayOrder": 3},
        description=description,
        targetType={"workoutTargetTypeId": TargetType.NO_TARGET, "workoutTargetTypeKey": "no.target", "displayOrder": 1}
    )
    
    # Intentar millorar la visualització afegint camps extra (tot i que l'API pot ignorar-los si no coincideixen amb la DB)
    # create_strength_step és un mètode custom, però ExecutableStep permet extra fields.
    # No obstant, el més important és el stepOrder únic.
    
    if duration and duration > 0:
        step.endCondition = {
            "conditionTypeId": ConditionType.TIME, 
            "conditionTypeKey": "time", 
            "displayOrder": 2, 
            "displayable": True
        }
        step.endConditionValue = float(duration)
    else:
        # Lap Button / Open Reps Condition (ID 7)
        # Usar ITERATIONS (7) sense valor (None) permet que el rellotge mostri "--" reps
        # i esperi indefinidament fins que l'usuari premi Lap.
        # ID 8 (LAP) era "fixed.rest" i mostrava un temps erroni (1193h).
        step.endCondition = {
            "conditionTypeId": 7, 
            "conditionTypeKey": "iterations", 
            "displayOrder": 7, 
            "displayable": True
        }
        step.endConditionValue = None

    return step

def main():
    client = get_garmin_client()
    
    # --- DILLUNS 16: FORÇA A ---
    # Escalfament
    step_warmup = ExecutableStep(
        stepOrder=1,
        stepType={"stepTypeId": StepType.WARMUP, "stepTypeKey": "warmup", "displayOrder": 1},
        endCondition={"conditionTypeId": ConditionType.TIME, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
        endConditionValue=8 * 60,
        description="Escalfament: Mobilitat + Caminada Ràpida"
    )

    # Circuit x3
    # Mantenim ordre relatiu dins del circuit (1..5), però el RepeatGroup té el seu propi stepOrder (2)
    # Garmin sovint reenumera, però és millor ser explícit.
    exercises_a = [
        create_strength_step("Sentadilla (12-15 reps) [Lap]", 1),
        create_strength_step("Flexions (8-12 reps) [Lap]", 2),
        create_strength_step("Pont gluti (15 reps) [Lap]", 3),
        create_strength_step("Rem o Isomètric Escàpula (12 reps) [Lap]", 4),
        create_strength_step("Planxa (45s)", 5, duration=45)
    ]
    
    circuit_group = RepeatGroup(
        stepOrder=2,
        numberOfIterations=3,
        workoutSteps=exercises_a,
        smartRepeat=False
    )

    # Calma
    step_cooldown = ExecutableStep(
        stepOrder=3,
        stepType={"stepTypeId": StepType.COOLDOWN, "stepTypeKey": "cooldown", "displayOrder": 2},
        endCondition={"conditionTypeId": ConditionType.TIME, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
        endConditionValue=5 * 60,
        description="Tornada a la calma"
    )

    workout_mon = FitnessEquipmentWorkout(
        workoutName="Força A (45 min) v5", # v5
        description="Circuit x3: Sentadilla, Flexions, Pont, Rem, Planxa",
        estimatedDurationInSecs=45 * 60,
        workoutSegments=[{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": SportType.FITNESS_EQUIPMENT, "sportTypeKey": "fitness_equipment", "displayOrder": 6},
            "workoutSteps": [step_warmup, circuit_group, step_cooldown]
        }]
    )
    
    # PATCH manual per canviar SportType a Strength (20)
    # SportType.FITNESS_EQUIPMENT = 6. Strength = 20.
    workout_mon.workoutSegments[0].sportType["sportTypeId"] = 20
    workout_mon.workoutSegments[0].sportType["sportTypeKey"] = "strength_training"
    
    create_and_schedule(client, workout_mon, "2026-02-16")

    # --- DIMECRES 18: RUNNING SUAU (No toquem) ---
    
    # --- DIVENDRES 20: FORÇA B ---
    
    # Escalfament
    step_warmup_b = ExecutableStep(
        stepOrder=1,
        stepType={"stepTypeId": StepType.WARMUP, "stepTypeKey": "warmup", "displayOrder": 1},
        endCondition={"conditionTypeId": ConditionType.TIME, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
        endConditionValue=8 * 60,
        description="Escalfament"
    )

    # Circuit x3
    exercises_b = [
        create_strength_step("Zancada (10/10) [Lap]", 1),
        create_strength_step("Pike Push-up (8-12) [Lap]", 2),
        create_strength_step("Peso Mort Unilat (10/10) [Lap]", 3),
        create_strength_step("Fons Tríceps (10-12) [Lap]", 4),
        create_strength_step("Dead Bug (10/10) [Lap]", 5)
    ]
    
    circuit_group_b = RepeatGroup(
        stepOrder=2,
        numberOfIterations=3,
        workoutSteps=exercises_b,
        smartRepeat=False
    )

    step_cooldown_b = ExecutableStep(
        stepOrder=3,
        stepType={"stepTypeId": StepType.COOLDOWN, "stepTypeKey": "cooldown", "displayOrder": 2},
        endCondition={"conditionTypeId": ConditionType.TIME, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
        endConditionValue=5 * 60,
        description="Tornada calma"
    )

    workout_fri = FitnessEquipmentWorkout(
        workoutName="Força B (45 min) v5", # v5
        description="Circuit x3: Zancada, Pike Pushup, PM Unilat, Fons, Dead Bug",
        estimatedDurationInSecs=45 * 60,
        workoutSegments=[{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": SportType.FITNESS_EQUIPMENT, "sportTypeKey": "fitness_equipment", "displayOrder": 6},
            "workoutSteps": [step_warmup_b, circuit_group_b, step_cooldown_b]
        }]
    )
    
    # PATCH manual per canviar SportType a Strength (20)
    workout_fri.workoutSegments[0].sportType["sportTypeId"] = 20
    workout_fri.workoutSegments[0].sportType["sportTypeKey"] = "strength_training"
    
    create_and_schedule(client, workout_fri, "2026-02-20")

    # --- DISSABTE i DIUMENGE ja estaven bé (Running/Walking) ---
    # No els tornem a programar.

if __name__ == "__main__":
    main()
