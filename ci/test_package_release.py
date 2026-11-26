import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from package_release import package, release_files
from publish_release import verify_files


class FirmwareArchive(unittest.TestCase):
    def test_archive_keeps_the_pair_and_verifies_renamed_board_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = "aiui-v1-emmc-11.26-r7.img"
            manifest = Path(image).with_suffix(".json").name
            payload = b"\0" * 65536 + b"RKdev"
            metadata = json.dumps({"image": {"name": image, "bytes": len(payload),
                                            "sha256": hashlib.sha256(payload).hexdigest()}}).encode()
            (root / image).write_bytes(payload)
            (root / manifest).write_bytes(metadata)
            (root / "u-boot-rockchip.bin").write_bytes(b"loader")
            package(root, "aiui-3588", "aiui", "emmc", "11.26-r7")
            files = release_files("aiui-3588", "emmc", "11.26-r7")
            self.assertEqual(files[0], "aiui-3588-v1-emmc-11.26-r7.zip")
            with ZipFile(root / files[0]) as archive:
                self.assertEqual(archive.namelist(), [image, manifest])
                self.assertEqual(archive.read(image), payload)
                self.assertEqual(archive.read(manifest), metadata)
            self.assertEqual(set(verify_files(files, root)), set(files))
            (root / files[0]).write_bytes(b"corrupted zip")
            with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
                verify_files(files, root)

    def test_refuses_archive_if_image_does_not_match_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = "bdy-g98-v1-spi-11.26-r8"
            (root / f"{image}.img").write_bytes(b"a")
            (root / f"{image}.json").write_text(json.dumps({"image": {
                "name": f"{image}.img", "bytes": 1, "sha256": hashlib.sha256(b"b").hexdigest()}}))
            with self.assertRaisesRegex(ValueError, "does not match"):
                package(root, "bdy-g98", "bdy-g98", "spi", "11.26-r8")
            self.assertEqual(list(root.glob("*.zip*")), [])
