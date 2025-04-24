#!/usr/bin/env python3
"""
Snapshot helper — builds zips from manifest files.

Manifest format (JSON):
[
  "relative/file.py",
  "folder/subfolder",          # copies whole directory tree
  "scripts"                    # ditto
]
"""

from __future__ import annotations
import os, json, shutil, zipfile, hashlib
from typing import List
from ... import config

# --------------------------------------------------------------------------- #
def _read_manifest(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

# --------------------------------------------------------------------------- #
def _add_file_to_zip(zipf: zipfile.ZipFile, src_path: str, arcname: str):
    zipf.write(src_path, arcname)
# --------------------------------------------------------------------------- #
def _add_dir_to_zip(zipf: zipfile.ZipFile, dir_path: str, arc_prefix: str = ""):
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, dir_path)
            _add_file_to_zip(zipf, src, os.path.join(arc_prefix, rel))

# --------------------------------------------------------------------------- #
def build_snapshot(manifest_path: str, output_zip: str) -> str:
    """
    Build a zip file described by *manifest_path*.
    Returns sha256 hex-digest of the archive.
    """
    entries = _read_manifest(manifest_path)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            if os.path.isdir(entry):
                _add_dir_to_zip(zf, entry, entry)
            elif os.path.isfile(entry):
                _add_file_to_zip(zf, entry, entry)
            else:
                print(f"Warning: manifest entry '{entry}' not found – skipped")

    # compute sha256
    h = hashlib.sha256()
    with open(output_zip, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    digest = h.hexdigest()
    return digest
