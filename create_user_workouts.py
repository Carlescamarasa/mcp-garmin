import argparse
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, cast

from garminconnect.workout import (
    ConditionType,
    ExecutableStep,
    FitnessEquipmentWorkout,
    RepeatGroup,
    RunningWorkout,
    StepType,
    TargetType,
    WorkoutSegment,
)

from server import _schedule_workout_internal, get_garmin_client


logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("create_user_workouts")


CARDIO_SPORT = {"sportTypeId": 6, "sportTypeKey": "cardio_training", "displayOrder": 6}
HIIT_SPORT = {"sportTypeId": 33, "sportTypeKey": "hiit", "displayOrder": 6}
RUNNING_SPORT = {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1}


def get_next_weekday(start_date: date, weekday: int) -> date:
    """Retorna la propera data per al weekday indicat (0=dilluns ... 6=diumenge)."""
    if weekday < 0 or weekday > 6:
        raise ValueError("weekday must be between 0 and 6")

    days_ahead = (weekday - start_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return start_date + timedelta(days=days_ahead)


def create_and_schedule(client: Any, workout: Any, day_str: str) -> dict[str, Any]:
    try:
        logger.info("Uploading workout: %s", workout.workoutName)
        payload = workout.model_dump(exclude_none=True, mode="json")
        response = client.upload_workout(payload)

        workout_id = response.get("workoutId")
        if not workout_id:
            return {
                "status": "error",
                "workoutName": workout.workoutName,
                "scheduledDate": day_str,
                "error": "Upload response without workoutId",
                "response": response,
            }

        logger.info("Scheduling workout %s for %s", workout_id, day_str)
        schedule_response = _schedule_workout_internal(client, str(workout_id), day_str)

        return {
            "status": "success",
            "workoutId": workout_id,
            "workoutName": workout.workoutName,
            "scheduledDate": day_str,
            "scheduleResponse": schedule_response,
        }
    except Exception as error:
        logger.exception("Error processing workout %s", workout.workoutName)
        return {
            "status": "error",
            "workoutName": workout.workoutName,
            "scheduledDate": day_str,
            "error": str(error),
        }


def create_step(
    description: str,
    step_type_id: int,
    step_type_key: str,
    end_condition_id: int,
    end_condition_key: str,
    end_condition_value: float | None,
    order: int,
    target_type_id: int = TargetType.NO_TARGET,
    target_type_key: str = "no.target",
) -> ExecutableStep:
    step = ExecutableStep(
        stepOrder=order,
        stepType={"stepTypeId": step_type_id, "stepTypeKey": step_type_key, "displayOrder": 1},
        targetType={
            "workoutTargetTypeId": target_type_id,
            "workoutTargetTypeKey": target_type_key,
            "displayOrder": 1,
        },
    )

    setattr(step, "description", description)

    step.endCondition = {
        "conditionTypeId": end_condition_id,
        "conditionTypeKey": end_condition_key,
        "displayOrder": 2,
        "displayable": True,
    }
    step.endConditionValue = float(end_condition_value) if end_condition_value is not None else None
    return step


def create_reps_step(description: str, reps: int, order: int) -> ExecutableStep:
    return create_step(
        description=description,
        step_type_id=StepType.INTERVAL,
        step_type_key="interval",
        end_condition_id=ConditionType.ITERATIONS,
        end_condition_key="iterations",
        end_condition_value=float(reps),
        order=order,
    )


def create_time_step(description: str, seconds: int, order: int) -> ExecutableStep:
    return create_step(
        description=description,
        step_type_id=StepType.INTERVAL,
        step_type_key="interval",
        end_condition_id=ConditionType.TIME,
        end_condition_key="time",
        end_condition_value=float(seconds),
        order=order,
    )


def create_rest_step(description: str, seconds: int, order: int) -> ExecutableStep:
    return create_step(
        description=description,
        step_type_id=StepType.REST,
        step_type_key="rest",
        end_condition_id=ConditionType.TIME,
        end_condition_key="time",
        end_condition_value=float(seconds),
        order=order,
    )


def build_workout_force_a() -> FitnessEquipmentWorkout:
    steps = [
        create_step(
            "Escalfament: mobilitat articular + jumping jacks/caminar ràpid",
            StepType.WARMUP,
            "warmup",
            ConditionType.TIME,
            "time",
            8 * 60,
            order=1,
        ),
        RepeatGroup(
            stepOrder=2,
            numberOfIterations=3,
            workoutSteps=[
                create_reps_step("Sentadillas (12-15 reps)", 15, 1),
                create_reps_step("Rem/Dominades assistides (10-12 reps)", 12, 2),
                create_reps_step("Zancadas enrere (10 per cama)", 20, 3),
                create_reps_step("Flexions (8-10 reps)", 10, 4),
                create_time_step("Planxa abdominal", 45, 5),
                create_rest_step("Descans entre voltes", 60, 6),
            ],
            smartRepeat=False,
        ),
        create_step(
            "Tornada a la calma: estiraments suaus (quàdriceps/isquios/esquena)",
            StepType.COOLDOWN,
            "cooldown",
            ConditionType.TIME,
            "time",
            5 * 60,
            order=3,
        ),
    ]

    segment = WorkoutSegment(
        segmentOrder=1,
        sportType=CARDIO_SPORT,
        workoutSteps=steps,
    )

    workout = FitnessEquipmentWorkout(
        workoutName="Força A (Cos Complet)",
        estimatedDurationInSecs=45 * 60,
        workoutSegments=[segment],
    )
    setattr(workout, "description", "Circuit x3: Squats, Rem, Zancadas, Flexions, Planxa")
    return workout


def build_workout_force_b() -> FitnessEquipmentWorkout:
    steps = [
        create_step(
            "Escalfament: mobilitat + rotacions de tronc + simulació de comba",
            StepType.WARMUP,
            "warmup",
            ConditionType.TIME,
            "time",
            8 * 60,
            order=1,
        ),
        RepeatGroup(
            stepOrder=2,
            numberOfIterations=3,
            workoutSteps=[
                create_reps_step("A1. Flexions", 10, 1),
                create_reps_step("A2. Pes mort a una cama (8/cama)", 16, 2),
                create_rest_step("Descans post A2", 45, 3),
            ],
            smartRepeat=False,
        ),
        RepeatGroup(
            stepOrder=3,
            numberOfIterations=3,
            workoutSteps=[
                create_reps_step("B1. Press d'hombros", 12, 1),
                create_reps_step("B2. Glute bridge", 15, 2),
                create_rest_step("Descans post B2", 45, 3),
            ],
            smartRepeat=False,
        ),
        RepeatGroup(
            stepOrder=4,
            numberOfIterations=3,
            workoutSteps=[
                create_reps_step("C1. Dead bug (reps totals)", 20, 1),
                create_rest_step("Descans", 45, 2),
            ],
            smartRepeat=False,
        ),
        create_step(
            "Tornada a la calma: estiraments pectoral i maluc",
            StepType.COOLDOWN,
            "cooldown",
            ConditionType.TIME,
            "time",
            5 * 60,
            order=5,
        ),
    ]

    segment = WorkoutSegment(
        segmentOrder=1,
        sportType=CARDIO_SPORT,
        workoutSteps=steps,
    )

    workout = FitnessEquipmentWorkout(
        workoutName="Força B (Cos Complet)",
        estimatedDurationInSecs=45 * 60,
        workoutSegments=[segment],
    )
    setattr(workout, "description", "Paired sets A/B + bloc final de core")
    return workout


def build_workout_force_c() -> FitnessEquipmentWorkout:
    steps = [
        create_step(
            "Escalfament: mobilitat dinàmica",
            StepType.WARMUP,
            "warmup",
            ConditionType.TIME,
            "time",
            8 * 60,
            order=1,
        ),
        RepeatGroup(
            stepOrder=2,
            numberOfIterations=5,
            workoutSteps=[
                create_time_step("Min 1: 15 sentadillas amb salt", 60, 1),
                create_time_step("Min 2: 10 burpees", 60, 2),
                create_time_step("Min 3: 20 mountain climbers", 60, 3),
                create_time_step("Min 4: descans total", 60, 4),
            ],
            smartRepeat=False,
        ),
        create_step(
            "Tornada a la calma: respiració i baixada de pulsacions",
            StepType.COOLDOWN,
            "cooldown",
            ConditionType.TIME,
            "time",
            5 * 60,
            order=3,
        ),
    ]

    segment = WorkoutSegment(
        segmentOrder=1,
        sportType=HIIT_SPORT,
        workoutSteps=steps,
    )

    workout = FitnessEquipmentWorkout(
        workoutName="Força C (Metabòlic / HIIT)",
        estimatedDurationInSecs=45 * 60,
        workoutSegments=[segment],
    )
    setattr(workout, "description", "EMOM 20': 5 cicles x 4 minuts")
    return workout


def build_workout_running_suau() -> RunningWorkout:
    steps = [
        create_step(
            "Escalfament: caminar o trot molt suau (Zona 1)",
            StepType.WARMUP,
            "warmup",
            ConditionType.TIME,
            "time",
            10 * 60,
            order=1,
            target_type_id=TargetType.NO_TARGET,
            target_type_key="no.target",
        ),
        create_step(
            "Carrera contínua suau (Zona 2)",
            StepType.INTERVAL,
            "interval",
            ConditionType.TIME,
            "time",
            45 * 60,
            order=2,
        ),
        create_step(
            "Tornada a la calma: caminar molt suau",
            StepType.COOLDOWN,
            "cooldown",
            ConditionType.TIME,
            "time",
            5 * 60,
            order=3,
        ),
    ]

    segment = WorkoutSegment(
        segmentOrder=1,
        sportType=RUNNING_SPORT,
        workoutSteps=cast(list[ExecutableStep | RepeatGroup], steps),
    )

    workout = RunningWorkout(
        workoutName="Running Suau (Tirada Llarga)",
        estimatedDurationInSecs=60 * 60,
        workoutSegments=[segment],
    )
    setattr(workout, "description", "10' Z1 + 45' Z2 + 5' caminant")
    return workout


PLAN_BUILDERS = [
    (0, build_workout_force_a),
    (2, build_workout_force_b),
    (4, build_workout_force_c),
    (5, build_workout_running_suau),
]


def summarize_workout(workout: Any) -> dict[str, Any]:
    payload = workout.model_dump(exclude_none=True, mode="json")
    segment = payload["workoutSegments"][0]
    top_steps = []
    for step in segment.get("workoutSteps", []):
        if "workoutSteps" in step:
            top_steps.append(
                {
                    "type": "repeat_group",
                    "iterations": step.get("numberOfIterations"),
                    "children": len(step.get("workoutSteps", [])),
                }
            )
        else:
            top_steps.append(
                {
                    "type": "step",
                    "stepType": (step.get("stepType") or {}).get("stepTypeKey"),
                    "description": step.get("description"),
                }
            )

    return {
        "workoutName": payload.get("workoutName"),
        "estimatedDurationInSecs": payload.get("estimatedDurationInSecs"),
        "topLevelSteps": top_steps,
    }


def run_plan(reference_date: date | None = None, dry_run: bool = False) -> list[dict[str, Any]]:
    start = reference_date or date.today()
    client = None if dry_run else get_garmin_client()

    results: list[dict[str, Any]] = []
    for weekday, builder in PLAN_BUILDERS:
        workout = builder()
        schedule_day = str(get_next_weekday(start, weekday))

        if dry_run:
            preview = summarize_workout(workout)
            preview["scheduledDate"] = schedule_day
            results.append(preview)
            continue

        results.append(create_and_schedule(client, workout, schedule_day))

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and schedule weekly user workouts.")
    parser.add_argument(
        "--from-date",
        help="Reference date in YYYY-MM-DD format (default: today).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build workouts without uploading/scheduling anything.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    reference_date = date.today()
    if args.from_date:
        reference_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()

    results = run_plan(reference_date=reference_date, dry_run=args.dry_run)
    print(
        json.dumps(
            {
                "dryRun": args.dry_run,
                "count": len(results),
                "items": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
