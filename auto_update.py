#!/usr/bin/env python3
"""
AgentRadar 自动更新脚本
功能：将新的每日情报 md 文件自动推送到 GitHub，触发 Netlify 自动部署
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# ============ 配置区 ============
# 从环境变量读取 GitHub Token，避免泄露
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "Znlsoc/agentradar"
SOURCE_DIR = Path("/Users/zhangxiaochi/WorkBuddy/20260420092252")
AGENTRADAR_DIR = Path("/Users/zhangxiaochi/WorkBuddy/20260425171554/agentradar")

if not GITHUB_TOKEN:
    print("❌ 错误：未设置 GITHUB_TOKEN 环境变量")
    print("   请运行：export GITHUB_TOKEN='你的Token'")
    sys.exit(1)
# ==============================

def run_cmd(cmd):
    """执行命令行指令"""
    print(f"执行: {cmd}")
    result = os.system(cmd)
    if result != 0:
        print(f"❌ 命令执行失败: {cmd}")
        return False
    return True

def get_new_md_files():
    """获取源目录中新增或更新的 md 文件"""
    source_files = list(SOURCE_DIR.glob("每日情报_*.md"))
    local_files = list((AGENTRADAR_DIR / "source").glob("每日情报_*.md"))

    local_names = {f.name for f in local_files}
    new_files = [f for f in source_files if f.name not in local_names]

    return new_files

def main():
    print("=" * 40)
    print("🤖 AgentRadar 自动更新脚本")
    print("=" * 40)

    # 1. 检查新文件
    new_files = get_new_md_files()

    if not new_files:
        print("📭 没有发现新的情报文件")
        print("   源目录:", SOURCE_DIR)
        print("   本地目录:", AGENTRADAR_DIR / "source")
        return

    print(f"\n📦 发现 {len(new_files)} 个新文件:")
    for f in new_files:
        print(f"   + {f.name}")

    # 2. 复制新文件到 source 目录
    print("\n📁 复制文件到 source 目录...")
    for f in new_files:
        dest = AGENTRADAR_DIR / "source" / f.name
        shutil.copy2(f, dest)
        print(f"   ✓ {f.name}")

    # 3. Git 操作
    print("\n🔄 提交并推送...")

    os.chdir(AGENTRADAR_DIR)

    # 添加所有变更
    if not run_cmd("git add ."):
        return

    # 检查是否有变更
    commit_result = os.popen("git status --short").read()
    if not commit_result.strip():
        print("📭 没有需要提交的变更")
        return

    # 创建提交
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"Update: {'; '.join([f.name for f in new_files])} @ {date_str}"

    if not run_cmd(f'git commit -m "{commit_msg}"'):
        return

    # 推送
    remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
    if not run_cmd(f"git push {remote_url} main --force"):
        return

    print("\n" + "=" * 40)
    print("✅ 更新成功！")
    print(f"   GitHub: https://github.com/{GITHUB_REPO}")
    print(f"   网站: https://agentradar.netlify.app")
    print("\n🚀 Netlify 正在自动构建中，请稍候 1-2 分钟...")
    print("=" * 40)

if __name__ == "__main__":
    main()
