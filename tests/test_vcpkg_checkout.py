"""Local Git history fixtures: no remote network or vcpkg download needed."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_vcpkg_checkout.py"
spec = importlib.util.spec_from_file_location("verify_vcpkg", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def command(*args):
    completed = subprocess.run(args, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


class CheckoutTests(unittest.TestCase):
    def test_complete_clone_and_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            origin = root / "origin"
            command("git", "init", "-q", str(origin))
            command("git", "-C", str(origin), "config", "user.email", "test@example.invalid")
            command("git", "-C", str(origin), "config", "user.name", "Test")
            for i in range(3):
                (origin / "port.txt").write_text(str(i), encoding="utf-8")
                command("git", "-C", str(origin), "add", "port.txt")
                command("git", "-C", str(origin), "commit", "-qm", f"version {i}")
            full = root / "full"
            command("git", "clone", "-q", str(origin), str(full))
            sha = command("git", "-C", str(full), "rev-parse", "HEAD")
            self.assertEqual(module.validate(full, sha), sha)
            # Simulate the recorded failure: a clone with a partial/promisor config.
            command("git", "-C", str(full), "config", "remote.origin.promisor", "true")
            with self.assertRaisesRegex(RuntimeError, "promisor"):
                module.validate(full, sha)
            command("git", "-C", str(full), "config", "--unset", "remote.origin.promisor")
            # Simulate a partial clone filter retained on the remote.
            command("git", "-C", str(full), "config", "remote.origin.partialclonefilter", "blob:none")
            with self.assertRaisesRegex(RuntimeError, "partial clone"):
                module.validate(full, sha)
            command("git", "-C", str(full), "config", "--unset", "remote.origin.partialclonefilter")
            shallow = root / "shallow"
            command("git", "clone", "--depth", "1", "-q", origin.as_uri(), str(shallow))
            with self.assertRaisesRegex(RuntimeError, "shallow"):
                module.validate(shallow, sha)
            with self.assertRaisesRegex(RuntimeError, "revision mismatch"):
                module.validate(full, "f" * 40)

    def test_requires_real_sha(self):
        with self.assertRaises(ValueError):
            module.validate(Path("."), "latest")


if __name__ == "__main__":
    unittest.main()
