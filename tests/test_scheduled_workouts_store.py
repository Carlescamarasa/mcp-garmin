import tempfile
import unittest
from pathlib import Path

import scheduled_workouts_store as store


class ScheduledWorkoutsStoreTests(unittest.TestCase):
    def test_upsert_and_list_by_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "scheduled_workouts_index.json")

            store.upsert_workout(
                path,
                {
                    "workoutId": "101",
                    "workoutName": "Força A",
                    "description": "Sessió A",
                    "date": "2026-02-16",
                    "sportType": "strength_training",
                },
            )
            store.upsert_workout(
                path,
                {
                    "workoutId": "102",
                    "workoutName": "Força B",
                    "description": "Sessió B",
                    "date": "2026-02-18",
                    "sportType": "strength_training",
                },
            )

            listed = store.list_workouts(path, start_date="2026-02-16", end_date="2026-02-17")
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["workoutId"], "101")

    def test_status_filter_limit_and_mark_deleted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "scheduled_workouts_index.json")

            for wid, day in (("201", "2026-02-16"), ("202", "2026-02-17"), ("203", "2026-02-18")):
                store.upsert_workout(
                    path,
                    {
                        "workoutId": wid,
                        "workoutName": f"Workout {wid}",
                        "description": "desc",
                        "date": day,
                        "sportType": "running",
                    },
                )

            store.mark_workout_deleted(path, "202")

            active_only = store.list_workouts(path, status="active", limit=10)
            all_items = store.list_workouts(path, status="all", limit=2)

            self.assertEqual(len(active_only), 2)
            self.assertEqual(len(all_items), 2)
            self.assertTrue(all(item["status"] in {"active", "deleted"} for item in all_items))

    def test_invalid_inputs_raise_clear_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "scheduled_workouts_index.json")

            with self.assertRaises(ValueError):
                store.upsert_workout(path, {"workoutName": "Missing id", "date": "2026-02-16"})

            with self.assertRaises(ValueError):
                store.list_workouts(path, start_date="2026-02-20", end_date="2026-02-16")

            with self.assertRaises(ValueError):
                store.list_workouts(path, status="unknown")


if __name__ == "__main__":
    unittest.main()
