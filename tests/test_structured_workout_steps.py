import tempfile
import unittest
from pathlib import Path
from typing import Any, cast

from workout_payload_utils import build_workout_payload
from workout_tools import manage_workout


class _FakeGarminClient:
    def __init__(self) -> None:
        self.last_uploaded_payload: dict[str, Any] | None = None
        self.last_put_payload: dict[str, Any] | None = None
        self.last_deleted_workout_id: str | None = None

    def upload_workout(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_uploaded_payload = payload
        return {"workoutId": "999"}

    def get_workout_by_id(self, workout_id: str) -> dict[str, Any]:
        return {
            "workoutId": str(workout_id),
            "workoutName": "Forca A (Cos Complet)",
            "description": "Descripcio antiga",
            "estimatedDurationInSecs": 2700,
            "sportType": {
                "sportTypeId": 20,
                "sportTypeKey": "strength_training",
                "displayOrder": 6,
            },
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": {
                        "sportTypeId": 20,
                        "sportTypeKey": "strength_training",
                        "displayOrder": 6,
                    },
                    "workoutSteps": [
                        {
                            "type": "ExecutableStepDTO",
                            "stepOrder": 1,
                            "description": "Escalfament",
                            "stepType": {
                                "stepTypeId": 1,
                                "stepTypeKey": "warmup",
                                "displayOrder": 1,
                            },
                            "endCondition": {
                                "conditionTypeId": 2,
                                "conditionTypeKey": "time",
                                "displayOrder": 2,
                                "displayable": True,
                            },
                            "endConditionValue": 300,
                            "targetType": {
                                "workoutTargetTypeId": 1,
                                "workoutTargetTypeKey": "no.target",
                                "displayOrder": 1,
                            },
                        }
                    ],
                }
            ],
        }

    def connectapi(self, path: str, method: str = "GET", json: Any = None) -> dict[str, Any]:
        if method == "PUT":
            self.last_put_payload = json
            return {"ok": True}
        if method == "DELETE":
            self.last_deleted_workout_id = path.rsplit("/", 1)[-1]
            return {"ok": True}
        return {"ok": True}


class StructuredWorkoutStepsTests(unittest.TestCase):
    def test_build_payload_maps_reps_and_time_steps(self):
        payload = build_workout_payload(
            name="Forca A",
            description="Sessio estructurada",
            sport_label="STRENGTH",
            duration_minutes=45,
            steps=[
                {
                    "type": "workout_step",
                    "stepOrder": 1,
                    "durationType": "reps",
                    "durationValue": 12,
                    "targetType": "no_target",
                    "description": "Sentadilla",
                },
                {
                    "type": "workout_step",
                    "stepOrder": 2,
                    "durationType": "time",
                    "durationValue": 60,
                    "description": "Descans",
                },
            ],
        )

        steps = payload["workoutSegments"][0]["workoutSteps"]
        self.assertEqual(payload["sportType"]["sportTypeKey"], "strength_training")
        self.assertEqual(steps[0]["type"], "ExecutableStepDTO")
        self.assertEqual(steps[0]["endCondition"]["conditionTypeKey"], "iterations")
        self.assertEqual(steps[0]["endConditionValue"], 12)
        self.assertEqual(steps[1]["stepType"]["stepTypeKey"], "rest")
        self.assertEqual(steps[1]["endCondition"]["conditionTypeKey"], "time")

    def test_build_payload_supports_repeat_groups_and_auto_order(self):
        payload = build_workout_payload(
            name="Intervals",
            description="Bloc repetit",
            sport_label="CARDIO",
            duration_minutes=45,
            steps=[
                {
                    "type": "repeat_group",
                    "iterations": 2,
                    "steps": [
                        {
                            "type": "workout_step",
                            "durationType": "time",
                            "durationValue": 30,
                            "description": "Sprint",
                            "stepType": "interval",
                        },
                        {
                            "type": "workout_step",
                            "durationType": "time",
                            "durationValue": 30,
                            "description": "Descans",
                        },
                    ],
                }
            ],
        )

        repeat_group = payload["workoutSegments"][0]["workoutSteps"][0]
        self.assertEqual(repeat_group["type"], "RepeatGroupDTO")
        self.assertEqual(repeat_group["stepOrder"], 1)
        self.assertEqual(repeat_group["workoutSteps"][0]["stepOrder"], 1)
        self.assertEqual(repeat_group["workoutSteps"][1]["stepOrder"], 2)
        self.assertEqual(payload["estimatedDurationInSecs"], 120)

    def test_build_payload_rejects_unknown_duration_type(self):
        with self.assertRaises(ValueError):
            build_workout_payload(
                name="Invalid",
                description="x",
                sport_label="CARDIO",
                duration_minutes=45,
                steps=[
                    {
                        "type": "workout_step",
                        "durationType": "laps",
                        "durationValue": 3,
                        "description": "Incompatible",
                    }
                ],
            )

    def test_manage_workout_create_accepts_steps_without_description(self):
        client = _FakeGarminClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = manage_workout(
                client=cast(Any, client),
                action="create",
                workout_date="2026-02-16",
                name="Forca A",
                description=None,
                sport_type="STRENGTH",
                duration_minutes=45,
                steps=[
                    {
                        "type": "workout_step",
                        "durationType": "reps",
                        "durationValue": 10,
                        "description": "Sentadilla",
                    }
                ],
                index_file=str(Path(tmpdir) / "scheduled_workouts_index.json"),
                schedule_workout_fn=lambda _client, _wid, _day: {"ok": True},
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "create")
        self.assertIsNotNone(client.last_uploaded_payload)
        assert client.last_uploaded_payload is not None
        self.assertEqual(client.last_uploaded_payload["description"], "Entrenament estructurat")

    def test_manage_workout_update_applies_steps_to_payload_structure(self):
        client = _FakeGarminClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = manage_workout(
                client=cast(Any, client),
                action="update",
                workout_id="1474362475",
                description="Nova estructura Forca A",
                sport_type="strength_training",
                steps=[
                    {
                        "type": "workout_step",
                        "durationType": "reps",
                        "durationValue": 12,
                        "description": "Sentadilla",
                    },
                    {
                        "type": "workout_step",
                        "durationType": "time",
                        "durationValue": 60,
                        "description": "Descans",
                    },
                ],
                index_file=str(Path(tmpdir) / "scheduled_workouts_index.json"),
                schedule_workout_fn=lambda _client, _wid, _day: {"ok": True},
            )

        self.assertEqual(result["status"], "success")
        self.assertIn("steps", result["changedFields"])
        self.assertTrue(result["structuredStepsApplied"])
        self.assertIsNotNone(client.last_put_payload)
        assert client.last_put_payload is not None
        segment_steps = client.last_put_payload["workoutSegments"][0]["workoutSteps"]
        self.assertEqual(segment_steps[0]["endCondition"]["conditionTypeKey"], "iterations")
        self.assertEqual(segment_steps[1]["stepType"]["stepTypeKey"], "rest")


if __name__ == "__main__":
    unittest.main()
