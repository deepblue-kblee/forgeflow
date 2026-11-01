#!/usr/bin/env python3
"""Mechanically distribute canonical documents; --check never writes files."""

import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    mappings = [
        (root / "docs/spec", root / "src/forgeflow/spec"),
        (root / "docs/adr", root / "src/forgeflow/templates/adr"),
        (root / "docs/adr", root / "src/forgeflow/adr"),
    ]
    drift = []
    has_unexpected = False
    for source, destination in mappings:
        expected = {path.name for path in source.iterdir() if path.is_file()}
        actual = {path.name for path in destination.iterdir() if path.is_file()} if destination.exists() else set()
        unexpected = actual - expected
        if unexpected:
            has_unexpected = True
            drift.extend(str(destination / name) for name in sorted(unexpected))
        for name in sorted(expected):
            src, dst = source / name, destination / name
            if not dst.is_file() or src.read_bytes() != dst.read_bytes():
                drift.append(str(dst.relative_to(root)))
                if not args.check:
                    destination.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
    source, destination = root / "docs/CHANGELOG.md", root / "src/forgeflow/CHANGELOG.md"
    if source.read_bytes() != destination.read_bytes():
        drift.append(str(destination.relative_to(root)))
        if not args.check:
            shutil.copyfile(source, destination)
    if args.check and drift:
        print("Distribution drift:\n" + "\n".join(drift))
        return 1
    print("Distribution documents match canonical sources." if not drift else "Synchronized distribution documents.")
    return 1 if has_unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
