#!/bin/bash
set -e

# ============================================================
# 华为云作品展览馆一键发布脚本（通用版）
# 用法: bash publish/publish-work.sh <项目名>
# 示例: bash publish/publish-work.sh calendar-2027
# 配置: 编辑 <项目名>/publish-config.json
# 前置: hcloud 已 configure set + Python + Playwright
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -z "$1" ]; then
  echo "用法: bash publish/publish-work.sh <项目名>"
  echo "示例: bash publish/publish-work.sh calendar-2027"
  exit 1
fi

PROJECT_NAME="$1"
PROJECT_DIR="$ROOT_DIR/$PROJECT_NAME"
CONFIG="$PROJECT_DIR/publish-config.json"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "ERROR: 项目目录 $PROJECT_DIR 不存在"
  exit 1
fi

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: 配置文件 $CONFIG 不存在"
  exit 1
fi

SCRIPT_DIR_WIN=$(cygpath -m "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")
CONFIG_WIN=$(cygpath -m "$CONFIG" 2>/dev/null || echo "$CONFIG")

DOMAIN_ID=$(python -c "import json;print(json.load(open(r'$CONFIG_WIN'))['domainId'])")
REGION=$(python -c "import json;print(json.load(open(r'$CONFIG_WIN'))['region'])")
WORK_NAME=$(python -c "import json;print(json.load(open(r'$CONFIG_WIN'))['workName'])")

echo "========================================"
echo "  华为云作品展览馆发布脚本"
echo "  项目: $PROJECT_NAME"
echo "  作品: $WORK_NAME"
echo "========================================"

# 导出项目目录供 Python 脚本使用
export PROJECT_DIR

# --- 检查环境变量 ---
if [ -z "$HUAWEICLOUD_SDK_AK" ] || [ -z "$HUAWEICLOUD_SDK_SK" ]; then
  echo "ERROR: 请先设置环境变量 HUAWEICLOUD_SDK_AK 和 HUAWEICLOUD_SDK_SK"
  exit 1
fi
echo "[1/7] 环境变量检查 ... OK"

# --- 创建 SELF_VERIFY 委托 (如果不存在) ---
echo -n "[2/7] 检查 SELF_VERIFY 委托 ... "
hcloud IAM CreateAgency \
  --cli-region=$REGION \
  --cli-domain-id=$DOMAIN_ID \
  --agency.name=SELF_VERIFY \
  --agency.domain_id=$DOMAIN_ID \
  --agency.trust_domain_id=$DOMAIN_ID \
  --agency.description="self verify" \
  --agency.duration=FOREVER 2>/dev/null && echo "已创建" || echo "已存在"

# --- 生成 STS 临时凭证 ---
echo -n "[3/7] 生成 STS 临时凭证 ... "
python "$SCRIPT_DIR/gen_sts.py" > /dev/null 2>&1 && echo "OK" || { echo "FAILED"; exit 1; }

# --- 生成封面 ---
echo -n "[4/7] 生成封面截图 ... "
python "$SCRIPT_DIR/generate_cover.py" > /dev/null 2>&1 && echo "OK" || { echo "FAILED (未找到可用浏览器)"; exit 1; }

# --- 打包 detail.zip ---
echo -n "[5/7] 打包详情包 ... "
python "$SCRIPT_DIR/pack_detail.py" > /dev/null 2>&1 && echo "OK" || { echo "FAILED"; exit 1; }

# --- 提交发布 ---
echo -n "[6/7] 准备提交数据 ... "
echo "OK"
echo ""
echo "[7/7] 提交到华为云作品展览馆 ..."
python "$SCRIPT_DIR/submit.py" && PUBLISH_OK=1 || PUBLISH_OK=0

echo ""
echo "========================================"
echo "  发布结果"
echo "========================================"
if [ "$PUBLISH_OK" = "1" ]; then
  echo "发布成功!"
  rm -f "$SCRIPT_DIR/sts-creds.json" "$SCRIPT_DIR/cover.png" "$SCRIPT_DIR/detail.zip"
  echo "临时产物已自动清理。"
else
  echo "发布失败，请检查上方错误信息。"
  echo "临时产物保留在 publish/ 目录供排查。"
fi