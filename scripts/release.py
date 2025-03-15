#!/usr/bin/env python3
"""
版本發布腳本。

用法：
    python scripts/release.py [版本號] [--push]

例如：
    python scripts/release.py 0.1.1        # 只更新版本號和創建標籤
    python scripts/release.py 0.1.1 --push # 更新版本號、創建標籤並推送到 GitHub
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def update_version(version):
    """更新所有文件中的版本號"""
    # 更新 __init__.py
    init_file = Path("playwright_mcp_fetch/__init__.py")
    content = init_file.read_text(encoding="utf-8")
    content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{version}"',
        content
    )
    init_file.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 {init_file}")

    # 更新 pyproject.toml
    pyproject_file = Path("pyproject.toml")
    content = pyproject_file.read_text(encoding="utf-8")
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{version}"',
        content
    )
    pyproject_file.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 {pyproject_file}")

    # 更新 setup.py
    setup_file = Path("setup.py")
    content = setup_file.read_text(encoding="utf-8")
    content = re.sub(
        r'version="[^"]+"',
        f'version="{version}"',
        content
    )
    setup_file.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 {setup_file}")
    
    # 更新 CHANGELOG.md
    update_changelog(version)

def update_changelog(version):
    """更新 CHANGELOG.md"""
    changelog_file = Path("CHANGELOG.md")
    if not changelog_file.exists():
        print(f"⚠️ {changelog_file} 不存在，跳過更新")
        return
    
    content = changelog_file.read_text(encoding="utf-8")
    
    # 獲取當前日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 將 [未發布] 替換為新版本
    new_version_header = f"## [{version}] - {today}"
    content = content.replace("## [未發布]", new_version_header)
    
    # 添加新的 [未發布] 部分
    unreleased_section = """## [未發布]

### 新增
- 

### 修改
- 

### 修復
- 
"""
    content = content.replace("# 更新日誌", "# 更新日誌\n\n" + unreleased_section)
    
    # 寫回文件
    changelog_file.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 {changelog_file}")

def git_commit_and_tag(version):
    """提交更改並創建標籤"""
    # 提交更改
    subprocess.run(["git", "add", "playwright_mcp_fetch/__init__.py", "pyproject.toml", "setup.py", "CHANGELOG.md"], check=True)
    subprocess.run(["git", "commit", "-m", f"Bump version to {version}"], check=True)
    print("✅ 已提交版本更新")

    # 創建標籤
    tag = f"v{version}"
    subprocess.run(["git", "tag", "-a", tag, "-m", f"Version {version}"], check=True)
    print(f"✅ 已創建標籤 {tag}")
    
    return tag

def push_changes(tag):
    """推送更改和標籤到 GitHub"""
    print("🚀 正在推送更改到 GitHub...")
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("✅ 已推送主分支更改")
    
    print(f"🚀 正在推送標籤 {tag} 到 GitHub...")
    subprocess.run(["git", "push", "origin", tag], check=True)
    print(f"✅ 已推送標籤 {tag}")
    
    print("\n🎉 GitHub Actions 將自動創建發布版本並發布到 PyPI")
    print(f"   請檢查: https://github.com/kevinwatt/playwright-mcp-fetch/actions")

def main():
    """主函數"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    version = sys.argv[1]
    auto_push = "--push" in sys.argv
    
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print("錯誤：版本號格式應為 X.Y.Z")
        sys.exit(1)

    print(f"🚀 準備發布版本 {version}...")
    update_version(version)
    tag = git_commit_and_tag(version)
    
    if auto_push:
        push_changes(tag)
    else:
        print(f"\n✨ 版本 {version} 準備就緒！")
        print("\n要完成發布，請運行以下命令：")
        print(f"git push origin main && git push origin {tag}")
        print("\n或者下次使用 --push 參數自動推送：")
        print(f"python scripts/release.py {version} --push")

if __name__ == "__main__":
    main() 