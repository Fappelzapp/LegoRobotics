# pyright: reportOptionalMemberAccess=false
"""Offline tests of PID.py, shared motion loops, and the limited laptop model.

No hub, transport, traction, or real motor behaviour is tested here.
"""

import ast
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests import _path  # noqa: F401
import PID as program
from lib import competition_config as config
from lib.competition_motion import HeadingPID
from lib.geometry import wrap_deg
from src.sim.competition import Simulation


class HeadingControllerTests(unittest.TestCase):
    def make_pid(self, **overrides):
        values = dict(kp=4, ki=0, kd=0.02, output_limit=180, integral_limit=30)
        values.update(overrides)
        return HeadingPID(**values)

    def test_corrects_heading_both_sides(self):
        self.assertLess(self.make_pid().update(0, 10, 0.02), 0)
        self.assertGreater(self.make_pid().update(0, -10, 0.02), 0)

    def test_error_wraps_across_180(self):
        self.assertAlmostEqual(self.make_pid().update(-179, 179, 0.02), 8)

    def test_derivative_wraps_sensor_boundary(self):
        pid = self.make_pid(kp=0, kd=1, output_limit=1000)
        pid.update(0, 179, 0.02)
        self.assertAlmostEqual(pid.update(0, -179, 0.02), -100)

    def test_derivative_uses_time_not_sample_count(self):
        slow = self.make_pid(kp=0, kd=1)
        fast = self.make_pid(kp=0, kd=1)
        slow.update(0, 0, 0.1)
        fast.update(0, 0, 0.02)
        self.assertAlmostEqual(slow.update(0, 1, 0.1), fast.update(0, 0.2, 0.02))

    def test_target_step_does_not_kick_derivative(self):
        pid = self.make_pid(kp=0, kd=1)
        pid.update(0, 0, 0.02)
        self.assertEqual(pid.update(90, 0, 0.02), 0)

    def test_integral_clamps_and_resets(self):
        pid = self.make_pid(kp=0, ki=1, kd=0, integral_limit=2)
        for _ in range(100):
            pid.update(0, -10, 0.02)
        self.assertEqual(pid.integral, 2)
        pid.reset()
        self.assertEqual(pid.integral, 0)
        self.assertIsNone(pid.previous_heading)

    def test_no_integration_further_into_saturation(self):
        pid = self.make_pid(kp=100, ki=1, kd=0)
        self.assertEqual(pid.update(20, 0, 0.02), 180)
        self.assertEqual(pid.integral, 0)

    def test_integral_disabled_does_not_accumulate(self):
        pid = self.make_pid()
        for _ in range(20):
            pid.update(0, 10, 0.02)
        self.assertEqual(pid.integral, 0)

    def test_bad_dt_and_nonfinite_sensor_are_rejected(self):
        for dt in (0, -1, float("nan"), float("inf")):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                self.make_pid().update(0, 0, dt)
        with self.assertRaises(ValueError):
            self.make_pid().update(0, float("nan"), 0.02)


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.world = Simulation()
        self.world.connect(program)
        self.motion = self.world.motion

    def assert_braked(self):
        self.assertEqual(self.world.drive.speed_command, 0)
        self.assertEqual(self.world.drive.turn_command, 0)
        self.assertGreater(self.world.drive.brake_count, 0)

    def test_uses_centimetres_and_speed_first(self):
        program.motors_pid(0, 300, 21)
        self.assertAlmostEqual(self.world.drive.distance(), 210, delta=2)
        self.assertTrue(all(v > 0 and w == 0 for v, w in self.world.drive.commands))
        self.assert_braked()

    def test_reverse_corrects_heading_in_same_body_direction(self):
        self.world.heading_deg = 10
        program.motors_pid(0, -200, 30)
        v, w = self.world.drive.commands[0]
        self.assertLess(v, 0)
        self.assertLess(w, 0)
        self.assertLess(abs(self.world.hub.imu.heading()), 1)
        self.assertLess(self.world.drive.distance(), 0)
        self.assert_braked()

    def test_successive_moves_use_a_baseline_not_a_gyro_reset(self):
        self.world.heading_deg = 30
        program.motors_pid(30, 200, 10)
        first = self.world.drive.distance()
        program.motors_pid(30, 200, 10)
        self.assertAlmostEqual(self.world.drive.distance() - first, 100, delta=2)
        self.assertAlmostEqual(self.world.hub.imu.heading(), 30)

    def test_loop_sleeps_twenty_ms_without_prints(self):
        waits = []
        real_wait = self.world.wait
        def record_wait(ms):
            waits.append(ms)
            real_wait(ms)
        self.motion.wait = record_wait
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            program.motors_pid(0, 150, 10)
        self.assertTrue(waits)
        self.assertEqual(set(waits), {20})
        self.assertEqual(stdout.getvalue(), "")

    def test_measures_real_dt_instead_of_assuming_exact_50_hz(self):
        used_dt = []
        update = self.motion.heading_pid.update
        def observe(target, heading, dt):
            used_dt.append(dt)
            return update(target, heading, dt)
        self.motion.heading_pid.update = observe
        self.motion.wait = lambda ms: self.world.wait(ms + 7)
        program.motors_pid(0, 200, 10)
        self.assertAlmostEqual(used_dt[0], 0.020)
        self.assertTrue(all(abs(dt - 0.027) < 1e-10 for dt in used_dt[1:]))

    def test_zero_distance_is_a_braked_noop(self):
        program.motors_pid(0, 0, 0)
        self.assertEqual(self.world.time_ms, 0)
        self.assert_braked()

    def test_invalid_moves_raise_and_brake(self):
        for values in ((0, 0, 1), (0, 100, -1), (float("nan"), 100, 1),
                       (0, float("inf"), 1), (0, 100, float("nan"))):
            with self.subTest(values=values), self.assertRaises(ValueError):
                program.motors_pid(*values)
            self.assert_braked()

    def test_blocked_encoder_times_out_and_brakes(self):
        self.world.blocked = True
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            self.motion.drive_heading(0, 200, 10, timeout_ms=100)
        self.assertEqual(self.world.time_ms, 100)
        self.assert_braked()

    def test_sensor_exception_brakes(self):
        with patch.object(self.world.hub.imu, "heading", side_effect=OSError("sensor unavailable")):
            with self.assertRaises(OSError):
                program.motors_pid(0, 200, 10)
        self.assert_braked()

    def test_turn_goes_short_way_through_180(self):
        self.world.heading_deg = 179
        program.ausrichten2(-170)
        self.assertGreater(self.world.drive.commands[0][1], 0)
        self.assertLess(abs(wrap_deg(-170 - self.world.hub.imu.heading())), 2)
        self.assertLess(self.world.heading_deg - 179, 15)
        self.assert_braked()

    def test_heading_360_is_equivalent_to_zero_not_a_full_rotation(self):
        program.ausrichten1(360)
        self.assertTrue(all(w == 0 for _, w in self.world.drive.commands))
        self.assertGreaterEqual(self.world.time_ms, config.TURN_SETTLE_MS)
        self.assert_braked()

    def test_frozen_gyro_times_out_alignment(self):
        with patch.object(self.world.hub.imu, "heading", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "alignment timed out"):
                self.motion.align(45, config.TURN_FAST_KP, timeout_ms=100)
        self.assert_braked()

    def test_curve_chooses_direction_and_handles_reverse(self):
        self.motion.curve(-15, -100, 20)
        v, w = self.world.drive.commands[0]
        self.assertLess(v, 0)
        self.assertLess(w, 0)
        self.assertLessEqual(abs(wrap_deg(-15 - self.world.hub.imu.heading())), 3)
        self.assert_braked()

    def test_curve_zero_turn_rate_cannot_hang(self):
        with self.assertRaises(ValueError):
            self.motion.curve(30, 100, 0)
        self.assert_braked()

    def test_frozen_gyro_times_out_curve(self):
        with patch.object(self.world.hub.imu, "heading", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "curve timed out"):
                self.motion.curve(45, 100, 10, timeout_ms=100)
        self.assert_braked()

    def test_timed_raw_motor_move_is_converted_to_straight_travel(self):
        program.timed_straight(200, 1000)
        v, w = self.world.drive.commands[0]
        self.assertAlmostEqual(v, 108.9085453244)
        self.assertEqual(w, 0)
        self.assert_braked()


class SimulatorTests(unittest.TestCase):
    def test_import_does_not_require_pybricks_or_initialise_hardware(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.path.insert(0, 'src'); import PID; "
             "assert PID.hub is None; assert 'pybricks' not in sys.modules"],
            cwd=root, capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_virtual_time_does_not_sleep_in_wall_time(self):
        world = Simulation()
        with patch("time.sleep", side_effect=AssertionError("real sleep")):
            watch = world.stopwatch()
            world.wait(1000)
        self.assertEqual(watch.time(), 1000)
        self.assertEqual(len(world.samples), 50)

    def test_same_inputs_have_identical_traces(self):
        traces = []
        for _ in range(2):
            world = Simulation(heading_deg=15)
            world.connect(program)
            program.motors_pid(0, 200, 30)
            traces.append(world.samples)
        self.assertEqual(traces[0], traces[1])

    def test_module_run_angle_signs_multiply_like_firmware(self):
        for speed, angle, expected in ((100, 90, 90), (100, -90, -90),
                                        (-100, 90, -90), (-100, -90, 90)):
            with self.subTest(speed=speed, angle=angle):
                world = Simulation()
                world.left_module.run_angle(speed, angle)
                self.assertAlmostEqual(world.left_module.angle(), expected)
        world = Simulation()
        world.left_module.run_angle(0, 90)
        self.assertEqual(world.time_ms, 0)

    def test_nonblocking_modules_overlap(self):
        world = Simulation()
        world.left_module.run_angle(100, 200, wait=False)
        world.right_module.run_angle(100, 100)
        self.assertEqual(world.time_ms, 1000)
        self.assertAlmostEqual(world.left_module.angle(), 100)
        world.wait(1000)
        self.assertAlmostEqual(world.left_module.angle(), 200)

    def test_slip_changes_ground_travel_not_encoder_distance(self):
        worlds = []
        for slip in (0, 0.2):
            world = Simulation(slip_fraction=slip)
            world.connect(program)
            program.motors_pid(0, 200, 30)
            worlds.append(world)
        self.assertEqual(worlds[0].drive.distance(), worlds[1].drive.distance())
        self.assertAlmostEqual(worlds[1].x_mm, 0.8 * worlds[0].x_mm)

    def test_shutdown_still_stops_modules_if_drive_disconnected(self):
        world = Simulation()
        world.connect(program)
        world.left_module.run_angle(100, 200, wait=False)
        world.right_module.run_angle(100, 200, wait=False)
        with patch.object(world.drive, "brake", side_effect=OSError("drive disconnected")):
            with self.assertRaises(OSError):
                program.stop_all()
        self.assertEqual(world.left_module.rate, 0)
        self.assertEqual(world.right_module.rate, 0)

    def test_route5_refuses_to_invent_a_collision(self):
        world = Simulation()
        world.connect(program)
        with self.assertRaises(NotImplementedError):
            program.run_route("5")
        self.assertEqual(world.drive.speed_command, 0)
        self.assertEqual(world.left_module.rate, 0)
        self.assertEqual(world.right_module.rate, 0)

    def test_all_route_variants_finish_in_model_with_explicit_stall_assumption(self):
        for route in ("1", "2", "3-left", "3-right", "4", "5", "6", "7"):
            with self.subTest(route=route):
                world = Simulation(assume_stall_ms=500)
                world.connect(program)
                program.run_route(route)
                self.assertEqual(world.drive.speed_command, 0)
                self.assertLess(world.time_ms, 60000)
                if route == "5":
                    self.assertTrue(any("stall is assumed" in text for text in world.assumptions))


class RunnerTests(unittest.TestCase):
    def run_export(self, *arguments):
        from src.sim.run_pid import main
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "replay.html"
            with redirect_stdout(io.StringIO()):
                status = main(["--output", str(output), *arguments])
            html = output.read_text()
            marker = '<script id="simulation-data" type="application/json">'
            payload = html.split(marker, 1)[1].split("</script>", 1)[0]
            csv_text = output.with_suffix(".csv").read_text()
            return status, html, json.loads(payload), csv_text

    def test_exports_python_samples_and_csv_without_external_assets(self):
        status, html, cases, csv_text = self.run_export()
        self.assertEqual(status, 0)
        self.assertEqual(cases[0]["name"], "demo")
        self.assertIsNone(cases[0]["error"])
        self.assertNotIn("__SAMPLES__", html)
        self.assertNotIn("__CSV__", html)
        self.assertNotIn('<script src=', html)
        self.assertIn("case,time_s,x_mm,y_mm", csv_text)
        self.assertGreater(len(cases[0]["samples"]), 100)

    def test_sweep_does_not_change_hub_configuration(self):
        before = (config.HEADING_KP, config.HEADING_KD)
        status, _, cases, _ = self.run_export("--sweep")
        self.assertEqual(status, 0)
        self.assertEqual([case["settings"]["kp"] for case in cases], [0, 1, 4, 8])
        self.assertEqual((config.HEADING_KP, config.HEADING_KD), before)

    def test_unmodelled_stall_reports_failure_and_returns_nonzero(self):
        status, _, cases, _ = self.run_export("--route", "5")
        self.assertEqual(status, 1)
        self.assertIn("NotImplementedError", cases[0]["error"])
        self.assertTrue(cases[0]["samples"])

    def test_rejects_nonfinite_cli_settings(self):
        from src.sim.run_pid import main
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
            main(["--slip", "nan"])
        self.assertEqual(result.exception.code, 2)

    def test_micropython_bundle_contains_every_local_dependency_if_compiler_installed(self):
        root = Path(__file__).resolve().parents[1]
        compiler = root / ".venv/bin/pybricksdev"
        if not compiler.exists():
            self.skipTest("optional local pybricksdev compiler is not installed")
        # Compilation is offline. Do not invoke `run`, USB or BLE in a test.
        probe = """
import asyncio
from pybricksdev.compile import compile_multi_file
blob = asyncio.run(compile_multi_file('src/PID.py', 6))
offset = 0
names = set()
while offset < len(blob):
    size = int.from_bytes(blob[offset:offset+4], 'little')
    offset += 4
    end = blob.index(b'\\0', offset)
    names.add(blob[offset:end].decode())
    offset = end + 1 + size
required = {'__main__', 'lib.competition_config', 'lib.competition_motion', 'lib.geometry'}
assert required <= names, sorted(required - names)
assert not any(name.startswith('sim') or name.startswith('pybricks.') for name in names), names
"""
        result = subprocess.run(
            [str(root / ".venv/bin/python"), "-c", probe], cwd=root,
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


# Preserve the mission *arguments* while deliberately changing their controller
# implementation. Comparison is against the archived paste, not the old HTML.
class _SourceCalls(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_While(self, node):
        return  # physical button gates and timed wheel loops are intentionally replaced

    def visit_For(self, node):
        if not isinstance(node.iter, ast.Call):
            raise TypeError("for-loop iterable is not a call")
        for _ in range(ast.literal_eval(node.iter.args[0])):
            for statement in node.body:
                self.visit(statement)

    def visit_Call(self, node):
        name = ast.unparse(node.func)
        if name in _MISSION_CALLS:
            self.calls.append((name, tuple(ast.literal_eval(a) for a in node.args),
                               {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}))


_MISSION_CALLS = {"motors_pid", "ausrichten1", "ausrichten2", "motors_kurve1",
                  "modull.run_angle", "modulr.run_angle", "modull.run_until_stalled"}


class MissionPreservationTests(unittest.TestCase):
    def test_all_motion_and_attachment_arguments_match_paste(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "docs/Attachments/PID-original-2026-10-28.py.txt").read_text()
        source = source[source.index("# Weg 1 (Steine)"):]
        markers = ["# Weg 1 (Steine)", "# Weg 2 (Umarmung)", "ausgewaehlter_weg = None",
                   "# Weg 4 (Schwinger)", "# Weg 5 (schwarz)", "# Weg 6 (Lore zum anderen Team)",
                   "# Weg 7 (Sachen in Kreis)"]
        bodies = {}
        for i, route in ((0, "1"), (1, "2"), (3, "4"), (4, "5"), (5, "6"), (6, "7")):
            start = source.index(markers[i])
            end = source.index(markers[i + 1]) if i + 1 < len(markers) else len(source)
            bodies[route] = ast.parse(source[start:end]).body
        variant_source = source[source.index('if ausgewaehlter_weg == "links":'):source.index(markers[3])]
        branch = ast.parse(variant_source).body[0]
        if not isinstance(branch, ast.If):
            raise TypeError("route variant does not start with an if")
        bodies["3-left"] = branch.body
        else_branch = branch.orelse[0]
        if not isinstance(else_branch, ast.If):
            raise TypeError("route variant has no elif branch")
        bodies["3-right"] = else_branch.body

        for route, body in bodies.items():
            with self.subTest(route=route):
                expected = _SourceCalls()
                for statement in body:
                    expected.visit(statement)
                world = Simulation(assume_stall_ms=500)
                world.connect(program)
                actual = []
                def record(name):
                    return lambda *args, **kwargs: actual.append((name, args, kwargs))
                with patch.object(program, "motors_pid", record("motors_pid")), \
                     patch.object(program, "ausrichten1", record("ausrichten1")), \
                     patch.object(program, "ausrichten2", record("ausrichten2")), \
                     patch.object(program, "motors_kurve1", record("motors_kurve1")), \
                     patch.object(program.modull, "run_angle", record("modull.run_angle")), \
                     patch.object(program.modulr, "run_angle", record("modulr.run_angle")), \
                     patch.object(program.modull, "run_until_stalled", record("modull.run_until_stalled")):
                    program.run_route(route)
                self.assertEqual(actual, expected.calls)


if __name__ == "__main__":
    unittest.main()
