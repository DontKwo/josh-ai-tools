import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path for dynamic import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import dead_assets

class TestDeadAssets(unittest.TestCase):
    """Tests the dead_assets module."""

    def setUp(self) -> None:
        """Sets up a temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.root_path = Path(self.test_dir).resolve()

        # Create standard asset directories
        (self.root_path / "public").mkdir()
        (self.root_path / "images").mkdir()
        (self.root_path / "src").mkdir()

        # Create assets
        self.used_asset = self.root_path / "public" / "logo.png"
        self.used_asset.write_bytes(b"0" * 1024)  # 1 KB

        self.unused_asset = self.root_path / "images" / "old_banner.jpg"
        self.unused_asset.write_bytes(b"0" * 2048)  # 2 KB

        # Create code file referencing the used asset
        self.code_file = self.root_path / "src" / "index.html"
        self.code_file.write_text('<img src="/public/logo.png" />', encoding="utf-8")

    def tearDown(self) -> None:
        """Cleans up the temporary directory."""
        for root, dirs, files in os.walk(self.root_path, topdown=False):
            for file_name in files:
                (Path(root) / file_name).unlink()
            for dir_name in dirs:
                (Path(root) / dir_name).rmdir()
        self.root_path.rmdir()

    def test_find_assets(self) -> None:
        """Tests that all assets are found correctly."""
        assets = dead_assets.find_assets(self.root_path)
        self.assertEqual(len(assets), 2)
        asset_names = {a.name for a in assets}
        self.assertIn("logo.png", asset_names)
        self.assertIn("old_banner.jpg", asset_names)

    def test_get_dead_assets(self) -> None:
        """Tests detection of unreferenced assets and size calculation."""
        dead_files, total_size = dead_assets.get_dead_assets(self.root_path)

        self.assertEqual(len(dead_files), 1)
        self.assertEqual(dead_files[0].name, "old_banner.jpg")
        self.assertEqual(total_size, 2048)

    def test_format_size(self) -> None:
        """Tests size formatting logic."""
        self.assertEqual(dead_assets.format_size(500), "500.00 B")
        self.assertEqual(dead_assets.format_size(1024), "1.00 KB")
        self.assertEqual(dead_assets.format_size(1536), "1.50 KB")
        self.assertEqual(dead_assets.format_size(1048576), "1.00 MB")

if __name__ == "__main__":
    unittest.main()
