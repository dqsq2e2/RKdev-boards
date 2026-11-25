import subprocess
import unittest
from unittest.mock import patch

from github import gh


class GitHubRetries(unittest.TestCase):
    def test_retries_temporary_server_failure(self):
        failure = subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 500 Internal Server Error")
        success = subprocess.CompletedProcess(["gh"], 0, stdout="done")
        with patch("github.subprocess.run", side_effect=[failure, success]) as request, patch("github.time.sleep"):
            self.assertEqual(gh("api", "repos/example/repo"), "done")
            self.assertEqual(request.call_count, 2)

    def test_permission_failure_returns_immediately(self):
        failure = subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 403 Forbidden")
        with patch("github.subprocess.run", side_effect=failure) as request:
            with self.assertRaises(subprocess.CalledProcessError):
                gh("api", "repos/example/repo")
            self.assertEqual(request.call_count, 1)
