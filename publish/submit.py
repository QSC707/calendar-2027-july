#!/usr/bin/env python3
"""提交作品到华为云作品展览馆 (multipart POST)"""
import json, os, sys, time, uuid, ssl, http.client
from urllib.parse import urlparse

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.environ.get('PROJECT_DIR', '')

if not project_dir:
    print("ERROR: PROJECT_DIR 环境变量未设置", file=sys.stderr)
    sys.exit(1)

with open(os.path.join(project_dir, "publish-config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

DOMAIN_ID = cfg["domainId"]
CAMP_ID = cfg["campId"]
WORK_NAME = cfg["workName"]
INTRODUCTION = cfg["introduction"]
GIT_URL = cfg["gitUrl"]
GIT_BRANCH = cfg["gitBranch"]
HOST = "gallery.developer.huaweicloud.com"
PATH = "/open-api-public/v1/gallery/works"

with open(os.path.join(script_dir, "sts-creds.json"), encoding="utf-8") as f:
    sts = json.load(f)

cover_path = os.path.join(script_dir, "cover.png")
detail_path = os.path.join(script_dir, "detail.zip")

idempotency_key = f"gallery-publish-{DOMAIN_ID}-{int(time.time())}-{uuid.uuid4().hex[:8]}"

boundary = "----PublishBoundary" + uuid.uuid4().hex
body_parts = []

def add_field(name, value):
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
    body_parts.append(value.encode("utf-8") + b"\r\n")

def add_file(name, filepath, content_type):
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        filedata = f.read()
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
    body_parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
    body_parts.append(filedata + b"\r\n")

add_field("trainingCampId", CAMP_ID)
add_field("workName", WORK_NAME)
add_field("introduction", INTRODUCTION)
add_field("gitUrl", GIT_URL)
add_field("gitBranch", GIT_BRANCH)
add_field("envUrl", "")
add_file("image", cover_path, "image/png")
add_file("detail", detail_path, "application/zip")
body_parts.append(f"--{boundary}--\r\n".encode())
body = b"".join(body_parts)

conn = http.client.HTTPSConnection(HOST, timeout=60)
headers = {
    "Content-Type": f"multipart/form-data; boundary={boundary}",
    "X-Tmp-Ak": sts["ak"],
    "X-Tmp-Sk": sts["sk"],
    "X-Security-Token": sts["token"],
    "Idempotency-Key": idempotency_key,
}

print(f"发布作品「{WORK_NAME}」...")
print(f"URL: https://{HOST}{PATH}")
print(f"Idempotency-Key: {idempotency_key}")
print(f"Body size: {len(body)} bytes")

try:
    conn.request("POST", PATH, body=body, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", errors="replace")
    print(f"\nHTTP {resp.status}")
    try:
        parsed = json.loads(raw)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
        if resp.status == 201:
            work = parsed.get("data", {}).get("work", {})
            print(f"\n#status=201")
            print(f"workId={work.get('id', '')}")
            print(f"workUrl={work.get('workUrl', parsed.get('data', {}).get('workUrl', ''))}")
    except Exception:
        print(raw[:3000])
    sys.exit(0 if resp.status == 201 else 1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    conn.close()