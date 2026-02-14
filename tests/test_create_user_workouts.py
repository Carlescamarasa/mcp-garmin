import unittest
from datetime import date

try:
    import create_user_workouts as workouts
except ModuleNotFoundError as import_error:  # pragma: no cover - environment-dependent
    workouts = None
    IMPORT_ERROR = import_error
else:
    IMPORT_ERROR = None


@unittest.skipIf(workouts is None, f"Missing dependencies: {IMPORT_ERROR}")
class CreateUserWorkoutsTests(unittest.TestCase):
    def test_get_next_weekday_rolls_to_next_week(self):
        # 2026-02-14 is Saturday
        start = date(2026, 2, 14)
        self.assertEqual(workouts.get_next_weekday(start, 0).isoformat(), "2026-02-16")
        self.assertEqual(workouts.get_next_weekday(start, 5).isoformat(), "2026-02-21")

    def test_force_a_contains_circuit_repeat_group(self):
        workout = workouts.build_workout_force_a()
        summary = workouts.summarize_workout(workout)

        self.assertEqual(summary["workoutName"], "Força A (Cos Complet)")
        self.assertEqual(len(summary["topLevelSteps"]), 3)
        self.assertEqual(summary["topLevelSteps"][1]["type"], "repeat_group")
        self.assertEqual(summary["topLevelSteps"][1]["iterations"], 3)
        self.assertEqual(summary["topLevelSteps"][1]["children"], 6)

    def test_force_b_contains_three_repeat_groups(self):
        workout = workouts.build_workout_force_b()
        summary = workouts.summarize_workout(workout)

        repeat_groups = [s for s in summary["topLevelSteps"] if s["type"] == "repeat_group"]
        self.assertEqual(summary["workoutName"], "Força B (Cos Complet)")
        self.assertEqual(len(repeat_groups), 3)
        self.assertTrue(all(group["iterations"] == 3 for group in repeat_groups))

    def test_force_c_contains_emom_block(self):
        workout = workouts.build_workout_force_c()
        summary = workouts.summarize_workout(workout)

        self.assertEqual(summary["workoutName"], "Força C (Metabòlic / HIIT)")
        self.assertEqual(summary["topLevelSteps"][1]["type"], "repeat_group")
        self.assertEqual(summary["topLevelSteps"][1]["iterations"], 5)
        self.assertEqual(summary["topLevelSteps"][1]["children"], 4)

    def test_running_workout_has_three_time_blocks(self):
        workout = workouts.build_workout_running_suau()
        summary = workouts.summarize_workout(workout)

        self.assertEqual(summary["workoutName"], "Running Suau (Tirada Llarga)")
        self.assertEqual(summary["estimatedDurationInSecs"], 3600)
        self.assertEqual(len(summary["topLevelSteps"]), 3)
        self.assertTrue(all(step["type"] == "step" for step in summary["topLevelSteps"]))


if __name__ == "__main__":
    unittest.main()
