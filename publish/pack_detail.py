#!/usr/bin/env python3
"""打包 detail.zip，结构: README.md@根 + resources/ 目录"""
import zipfile, os, sys

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
out_path = os.path.join(script_dir, "detail.zip")
readme = os.path.join(project_dir, "README.md")
resources_dir = os.path.join(project_dir, "resources")

with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
    if os.path.exists(readme):
        z.write(readme, "README.md")
    z.writestr("resources/", "")
    if os.path.isdir(resources_dir):
        for f in os.listdir(resources_dir):
            full = os.path.join(resources_dir, f)
            if os.path.isfile(full):
                z.write(full, f"resources/{f}")

size = os.path.getsize(out_path)
print(f"detail.zip: {size} bytes")
if size < 1024:
    print("ERROR: detail.zip 小于 1024 bytes", file=sys.stderr)
    sys.exit(1)