import unittest
import tomllib
from pathlib import Path

from main import status


class StatusVersionTests(unittest.IsolatedAsyncioTestCase):
    async def test_status_uses_project_metadata_version(self):
        project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual((await status())["version"], project["project"]["version"])


if __name__ == "__main__":
    unittest.main()
