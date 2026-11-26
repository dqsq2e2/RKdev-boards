import copy
import subprocess
import unittest
from unittest.mock import patch

from publish_release import VERSION_MARKER, cleanup, ensure_release, publish, reset_legacy_releases


REPO = "owner/boards"
REPO_PATH = f"repos/{REPO}"
COMMIT = "a" * 40
TAG = "bearkey-bq3588c-emmc-2026-v11.26-r2"
EXPECTED = {"firmware.img": (1024, "sha256:abc")}


def release(tag=TAG, number=1, draft=False):
    return {"id": number, "tag_name": tag, "draft": draft, "prerelease": False,
            "body": VERSION_MARKER,
            "published_at": None if draft else "2026-11-26T00:00:00Z",
            "html_url": f"https://github.com/{REPO}/releases/tag/{tag}",
            "assets": [{"name": name, "size": size, "digest": digest, "state": "uploaded"}
                       for name, (size, digest) in EXPECTED.items()]}


class PublishRecovery(unittest.TestCase):
    def setUp(self):
        self.current = release(draft=True)
        self.ref = {"object": {"type": "commit", "sha": COMMIT}}

    def api(self, *args, **kwargs):
        if args[0].endswith("/git/ref/tags/" + TAG):
            return self.ref
        if args[0] == f"{REPO_PATH}/releases/1":
            return copy.deepcopy(self.current)
        raise AssertionError(args)

    def gh(self, *args, **kwargs):
        if args[:2] == ("release", "edit"):
            self.current.update(draft=False, published_at="2026-11-26T00:00:00Z")
        return ""

    def test_create_500_after_server_created_draft_resumes_existing_release(self):
        failure = subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 500 Internal Server Error")
        with patch("publish_release.list_releases", side_effect=[[], [self.current]]), \
                patch("publish_release.optional_api", return_value=None), \
                patch("publish_release.api", side_effect=[failure, self.current, self.current, self.ref]) as request, \
                patch("publish_release.gh", side_effect=self.gh), patch("publish_release.time.sleep"):
            result = ensure_release(REPO, COMMIT, TAG, "title", list(EXPECTED), EXPECTED)
            self.assertFalse(result["draft"])
            self.assertEqual(sum(call.args[0] == "--method" for call in request.call_args_list), 1)

    def test_partial_upload_is_completed_before_publishing(self):
        self.current["assets"] = []

        def upload(*args, **kwargs):
            if args[:2] == ("release", "upload"):
                self.current["assets"] = release()["assets"]
            return self.gh(*args, **kwargs)

        with patch("publish_release.list_releases", return_value=[self.current]), \
                patch("publish_release.optional_api", return_value=self.ref), \
                patch("publish_release.api", side_effect=self.api), \
                patch("publish_release.gh", side_effect=upload) as request:
            self.assertFalse(ensure_release(REPO, COMMIT, TAG, "title", list(EXPECTED), EXPECTED)["draft"])
            self.assertEqual(request.call_args_list[0].args[:2], ("release", "upload"))

    def test_published_matching_release_can_be_retried(self):
        self.current = release()
        with patch("publish_release.list_releases", return_value=[self.current]), \
                patch("publish_release.optional_api", return_value=self.ref), \
                patch("publish_release.api", side_effect=self.api), patch("publish_release.gh") as request:
            self.assertEqual(ensure_release(REPO, COMMIT, TAG, "title", list(EXPECTED), EXPECTED), self.current)
            request.assert_not_called()

    def test_different_commit_is_rejected(self):
        wrong = {"object": {"type": "commit", "sha": "b" * 40}}
        with patch("publish_release.list_releases", return_value=[self.current]), \
                patch("publish_release.optional_api", return_value=wrong):
            with self.assertRaisesRegex(ValueError, "another commit"):
                ensure_release(REPO, COMMIT, TAG, "title", list(EXPECTED), EXPECTED)

    def test_wrong_asset_digest_is_rejected(self):
        self.current = release()
        self.current["assets"][0]["digest"] = "sha256:wrong"
        with patch("publish_release.list_releases", return_value=[self.current]), \
                patch("publish_release.optional_api", return_value=self.ref), \
                patch("publish_release.api", side_effect=self.api):
            with self.assertRaisesRegex(ValueError, "verified build"):
                ensure_release(REPO, COMMIT, TAG, "title", list(EXPECTED), EXPECTED)


class Retention(unittest.TestCase):
    def test_first_new_scheme_build_removes_legacy_release_and_tags(self):
        legacy = release("bearkey-bq3588c-emmc-2026-v11.26-r14", 7)
        legacy["body"] = "旧版本说明"

        def refs(path):
            return [{"ref": f"refs/tags/{legacy['tag_name']}"}] if "/bearkey-" in path else []

        with patch("publish_release.api", side_effect=refs), \
                patch("publish_release.delete_resource") as remove:
            reset_legacy_releases(REPO_PATH, [legacy], "bearkey-bq3588c", "bq3588c", "emmc")
            self.assertEqual({call.args[0] for call in remove.call_args_list}, {
                f"{REPO_PATH}/releases/7", f"{REPO_PATH}/git/refs/tags/{legacy['tag_name']}"})

    def test_cleans_old_release_and_orphan_tags_for_renamed_package_only(self):
        current = release()
        old = release("bq3588c-emmc-v0.1-ci.21", 2)
        spi = release("bearkey-bq3588c-spi-2026-v11.26-r1", 3)
        newer = release("bearkey-bq3588c-emmc-2026-v11.26-r3", 4, draft=True)
        other = release("phx-r3588-emmc-v0.1-ci.28", 5)
        inputs = release("rkdev-firmware-inputs-v1", 6)
        orphan = "bq3588c-emmc-v0.1-dev.17"

        def refs(path):
            names = [current["tag_name"], newer["tag_name"]] if "/bearkey-" in path else [old["tag_name"], orphan]
            return [{"ref": f"refs/tags/{name}"} for name in names]

        with patch("publish_release.list_releases", return_value=[current, old, spi, newer, other, inputs]), \
                patch("publish_release.api", side_effect=refs), patch("publish_release.delete_resource") as remove:
            cleanup(REPO_PATH, current, "bearkey-bq3588c", "bq3588c", "emmc")
            self.assertEqual({call.args[0] for call in remove.call_args_list}, {
                f"{REPO_PATH}/releases/2", f"{REPO_PATH}/git/refs/tags/{old['tag_name']}",
                f"{REPO_PATH}/git/refs/tags/{orphan}"})

    def test_older_build_finishing_later_keeps_newer_release(self):
        newest = release("bearkey-bq3588c-emmc-2026-v11.26-r3")
        with patch("publish_release.verify_files", return_value=EXPECTED), \
                patch("publish_release.list_releases", return_value=[newest]), \
                patch("publish_release.ensure_release") as create, patch("publish_release.cleanup") as remove:
            publish(REPO, COMMIT, "bearkey-bq3588c", "bq3588c", "emmc", "11.26-r2", "2026-11-26")
            create.assert_not_called()
            remove.assert_not_called()
