import unittest

from build_version import version_for_run


DEFAULTS = {"bdy-g98": "spi", "phx-r3588": "emmc"}


def run(number, created, board="bdy-g98", profile="spi", workflow=1, current=True):
    title = f"RKdev 构建 {board} · {profile}" if current else f"构建 {board} · {profile}"
    return {"run_number": number, "created_at": created, "workflow_id": workflow,
            "display_title": title}


class CloudVersions(unittest.TestCase):
    def test_beijing_date_boundary_and_next_day(self):
        runs = [run(20, "2026-11-25T15:59:59Z"), run(21, "2026-11-25T16:00:00Z"),
                run(22, "2026-11-26T08:00:00Z"), run(23, "2026-11-26T16:00:00Z")]
        self.assertEqual(version_for_run(runs[1], runs, "bdy-g98", "spi", DEFAULTS),
                         ("11.26-r1", "2026-11-26"))
        self.assertEqual(version_for_run(runs[2], runs, "bdy-g98", "spi", DEFAULTS),
                         ("11.26-r2", "2026-11-26"))
        self.assertEqual(version_for_run(runs[3], runs, "bdy-g98", "spi", DEFAULTS),
                         ("11.27-r1", "2026-11-27"))

    def test_board_and_profile_have_independent_sequences(self):
        runs = [
            run(40, "2026-11-26T00:00:00Z", "bdy-g98", "spi"),
            run(41, "2026-11-26T00:01:00Z", "bdy-g98", "emmc"),
            run(42, "2026-11-26T00:02:00Z", "phx-r3588", "emmc"),
            run(43, "2026-11-26T00:03:00Z", "bdy-g98", "spi"),
            run(44, "2026-11-26T00:04:00Z", "bdy-g98", "emmc"),
        ]
        self.assertEqual(version_for_run(runs[3], runs, "bdy-g98", "spi", DEFAULTS)[0], "11.26-r2")
        self.assertEqual(version_for_run(runs[4], runs, "bdy-g98", "emmc", DEFAULTS)[0], "11.26-r2")
        self.assertEqual(version_for_run(runs[2], runs, "phx-r3588", "emmc", DEFAULTS)[0], "11.26-r1")

    def test_default_input_uses_the_board_default_profile(self):
        runs = [
            run(50, "2026-11-26T00:00:00Z", "bdy-g98", "default"),
            run(51, "2026-11-26T00:01:00Z", "bdy-g98", "spi"),
            run(52, "2026-11-26T00:02:00Z", "phx-r3588", "default"),
        ]
        self.assertEqual(version_for_run(runs[1], runs, "bdy-g98", "spi", DEFAULTS)[0], "11.26-r2")
        self.assertEqual(version_for_run(runs[2], runs, "phx-r3588", "emmc", DEFAULTS)[0], "11.26-r1")

    def test_legacy_run_names_do_not_enter_the_new_sequence(self):
        current = run(60, "2026-11-26T00:00:00Z", "bdy-g98", "spi")
        legacy = run(59, "2026-11-26T00:00:00Z", "bdy-g98", "spi", current=False)
        self.assertEqual(version_for_run(current, [legacy, current], "bdy-g98", "spi", DEFAULTS)[0],
                         "11.26-r1")

    def test_failure_and_rerun_keep_their_original_sequence(self):
        failed = {**run(70, "2026-11-26T00:00:00Z"), "conclusion": "failure"}
        rerun = {**failed, "run_attempt": 2}
        later = run(71, "2026-11-26T01:00:00Z")
        self.assertEqual(version_for_run(rerun, [failed, later], "bdy-g98", "spi", DEFAULTS),
                         ("11.26-r1", "2026-11-26"))
        self.assertEqual(version_for_run(later, [failed, later], "bdy-g98", "spi", DEFAULTS),
                         ("11.26-r2", "2026-11-26"))

    def test_other_workflows_do_not_change_version(self):
        current = run(80, "2027-01-01T00:00:00Z")
        other = run(1, current["created_at"], workflow=2)
        self.assertEqual(version_for_run(current, [other], "bdy-g98", "spi", DEFAULTS),
                         ("1.1-r1", "2027-01-01"))
