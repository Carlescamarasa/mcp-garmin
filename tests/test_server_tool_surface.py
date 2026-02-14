import ast
import unittest
from pathlib import Path


SERVER_PATH = Path(__file__).resolve().parents[1] / "server.py"


def _mcp_tools() -> dict[str, str]:
    tree = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
    tools: dict[str, str] = {}

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        has_mcp_decorator = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if isinstance(decorator.func.value, ast.Name):
                    if decorator.func.value.id == "mcp" and decorator.func.attr == "tool":
                        has_mcp_decorator = True
                        break

        if not has_mcp_decorator:
            continue

        tools[node.name] = ast.get_docstring(node) or ""

    return tools


class ServerToolSurfaceTests(unittest.TestCase):
    def test_tool_surface_is_simplified(self):
        tools = _mcp_tools()

        expected_tools = {
            "get_daily_health",
            "get_sleep_data",
            "get_stress_data",
            "get_body_battery",
            "get_body_composition",
            "get_training_status",
            "get_training_readiness",
            "get_endurance_score",
            "get_hill_score",
            "get_max_metrics",
            "list_activities",
            "get_activity_detail",
            "get_devices",
            "get_user_profile",
            "get_personal_records",
            "get_gear",
            "get_workouts",
            "schedule_user_week_plan",
        }
        self.assertEqual(set(tools), expected_tools)

    def test_redundant_tools_are_not_exposed(self):
        tools = _mcp_tools()
        disabled_by_design = {
            "get_device_settings",
            "get_device_last_used",
            "get_floors",
            "get_heart_rates",
            "get_stats_and_body",
            "get_user_summary",
            "get_hydration_data",
            "get_respiration_data",
            "get_spo2_data",
            "get_activity_splits",
            "get_activity_weather",
            "get_activity_hr_zones",
            "get_activity_power_zones",
            "get_privacy_settings",
            "get_badges",
            "download_activity_file",
            "get_steps_data",
            "create_running_workout",
            "get_calendar",
        }
        self.assertTrue(disabled_by_design.isdisjoint(set(tools)))

    def test_tool_descriptions_are_informative(self):
        tools = _mcp_tools()
        for name, docstring in tools.items():
            self.assertGreaterEqual(
                len(docstring.strip()),
                30,
                msg=f"Tool {name} should include a more detailed docstring",
            )


if __name__ == "__main__":
    unittest.main()
