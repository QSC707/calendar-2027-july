#!/usr/bin/env python3
"""生成华为云 STS 临时访问凭证 (通过 SELF_VERIFY 委托)"""
import json, os, sys, subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.environ.get('PROJECT_DIR', '')

if not project_dir:
    print("ERROR: PROJECT_DIR 环境变量未设置", file=sys.stderr)
    sys.exit(1)

with open(os.path.join(project_dir, "publish-config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

AK = os.environ.get('HUAWEICLOUD_SDK_AK', '')
SK = os.environ.get('HUAWEICLOUD_SDK_SK', '')
DOMAIN_ID = cfg["domainId"]
REGION = cfg["region"]

if not AK or not SK:
    print("ERROR: 请先设置环境变量 HUAWEICLOUD_SDK_AK 和 HUAWEICLOUD_SDK_SK", file=sys.stderr)
    sys.exit(1)

cmd = [
    "hcloud", "IAM", "CreateTemporaryAccessKeyByAgency",
    f"--cli-region={REGION}",
    f"--cli-domain-id={DOMAIN_ID}",
    "--auth.identity.assume_role.agency_name=SELF_VERIFY",
    "--auth.identity.methods.1=assume_role",
    f"--auth.identity.assume_role.domain_id={DOMAIN_ID}",
    "--auth.identity.assume_role.duration_seconds=3600",
]

result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
if result.returncode != 0:
    print(f"ERROR: {result.stderr}", file=sys.stderr)
    sys.exit(1)

try:
    resp = json.loads(result.stdout)
    credential = resp.get("credential", {})
    sts = {
        "ak": credential.get("access", ""),
        "sk": credential.get("secret", ""),
        "token": credential.get("securitytoken", ""),
        "expire": resp.get("token", {}).get("expires_at", "")
    }
    out_path = os.path.join(script_dir, "sts-creds.json")
    with open(out_path, "w", encoding='utf-8') as f:
        json.dump(sts, f, indent=2)
    print(json.dumps(sts, indent=2))
except Exception as e:
    print(f"PARSE ERROR: {e}", file=sys.stderr)
    print(result.stdout, file=sys.stderr)
    sys.exit(1)