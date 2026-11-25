import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from firmware_bundle import unpack


class FirmwareDirectories(unittest.TestCase):
    def test_accepts_formal_and_existing_firmware_directories(self):
        data = b"firmware input"
        files = {"ddr.bin": hashlib.sha256(data).hexdigest()}
        for prefix in ("bearkey-bq3588c/", "bq3588c/", ""):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                bundle = root / "inputs.zip"
                with ZipFile(bundle, "w") as archive:
                    archive.writestr(prefix + "ddr.bin", data)
                unpack(bundle, "bq3588c", files, root, "bearkey-bq3588c")
                self.assertEqual((root / "ddr.bin").read_bytes(), data)
