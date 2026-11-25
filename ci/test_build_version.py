import unittest

from build_version import version_for_run


def run(number, created, workflow=1):
    return {"run_number": number, "created_at": created, "workflow_id": workflow}


class CloudVersions(unittest.TestCase):
    def test_beijing_date_boundary_and_next_day(self):
        runs = [run(20, "2026-11-25T15:59:59Z"), run(21, "2026-11-25T16:00:00Z"),
                run(22, "2026-11-26T08:00:00Z"), run(23, "2026-11-26T16:00:00Z")]
        self.assertEqual(version_for_run(runs[1], runs), ("11.26-r1", "2026-11-26"))
        self.assertEqual(version_for_run(runs[2], runs), ("11.26-r2", "2026-11-26"))
        self.assertEqual(version_for_run(runs[3], runs), ("11.27-r1", "2026-11-27"))

    def test_failure_and_rerun_keep_their_original_sequence(self):
        failed = {**run(30, "2026-11-26T00:00:00Z"), "conclusion": "failure"}
        rerun = {**failed, "run_attempt": 2}
        later = run(31, "2026-11-26T01:00:00Z")
        self.assertEqual(version_for_run(rerun, [failed, later]), ("11.26-r1", "2026-11-26"))
        self.assertEqual(version_for_run(later, [failed, later]), ("11.26-r2", "2026-11-26"))

    def test_other_workflows_do_not_change_version(self):
        current = run(2, "2027-01-01T00:00:00Z")
        self.assertEqual(version_for_run(current, [run(1, current["created_at"], workflow=2)]),
                         ("1.1-r1", "2027-01-01"))
