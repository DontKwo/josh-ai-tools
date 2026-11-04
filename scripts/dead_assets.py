import os
import argparse
from pathlib import Path
from typing import List, Tuple, Set

ASSET_DIRS = {"public", "assets", "images", "static"}
CODE_EXTENSIONS = {
    ".py", ".html", ".js", ".ts", ".css", ".scss", ".vue", ".jsx", ".tsx",
    ".md", ".json", ".txt", ".sh", ".yml", ".yaml", ".xml"
}

def find_assets(root_path: Path) -> List[Path]:
    """Finds all files inside standard asset directories."""
    found_assets = []
    for directory in ASSET_DIRS:
        target_dir = root_path / directory
        if target_dir.exists() and target_dir.is_dir():
            for root, _, files in os.walk(target_dir):
                for file_name in files:
                    found_assets.append(Path(root) / file_name)
    return found_assets

def extract_asset_names(assets: List[Path]) -> Set[str]:
    """Extracts base filenames from a list of asset paths."""
    return {asset.name for asset in assets}

def scan_codebase_for_references(root_path: Path, asset_names: Set[str]) -> Set[str]:
    """Scans all code files to find which assets are referenced."""
    referenced_assets = set()
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in ASSET_DIRS and not d.startswith(".")]
        for file_name in files:
            file_path = Path(root) / file_name
            if file_path.suffix in CODE_EXTENSIONS:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for asset_name in list(asset_names):
                        if asset_name in content:
                            referenced_assets.add(asset_name)
                            asset_names.remove(asset_name)
                except (UnicodeDecodeError, OSError):
                    continue
    return referenced_assets

def format_size(size_bytes: int) -> str:
    """Formats bytes into human-readable strings."""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.2f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.2f} TB"

def get_dead_assets(root_path: Path) -> Tuple[List[Path], int]:
    """Identifies unreferenced assets and calculates their total size."""
    all_assets = find_assets(root_path)
    asset_names = extract_asset_names(all_assets)

    referenced_names = scan_codebase_for_references(root_path, set(asset_names))

    unreferenced_assets = [
        asset for asset in all_assets
        if asset.name not in referenced_names
    ]

    total_size = sum(asset.stat().st_size for asset in unreferenced_assets)
    return unreferenced_assets, total_size

def main(directory_path: str) -> None:
    """Main execution entry point."""
    root_path = Path(directory_path).resolve()
    if not root_path.exists():
        print(f"Directory {directory_path} does not exist.")
        return

    dead_assets, total_size = get_dead_assets(root_path)

    print(f"Found {len(dead_assets)} unreferenced assets.")
    for asset in dead_assets:
        asset_size = format_size(asset.stat().st_size)
        print(f"{asset.relative_to(root_path)} - {asset_size}")

    print(f"Total reclaimable space: {format_size(total_size)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find dead assets in project.")
    parser.add_argument("path", nargs="?", default=".", help="Project root path")
    args = parser.parse_args()
    main(args.path)
