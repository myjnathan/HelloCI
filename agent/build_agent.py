#!/usr/bin/env python3
"""
CI Build Failure Agent
使用 DeepSeek API 自动分析并尝试修复构建失败

功能：
1. 监听 GitHub Actions 构建失败
2. 使用 DeepSeek 分析错误日志
3. 自动尝试修复并提交 PR

用法：
    python agent/build_agent.py [error_log_file]
    或在 GitHub Actions 中通过 stdin 传入日志
"""

import os
import sys
import json
import subprocess
import requests
from typing import Optional, Dict, Any

# ========== 配置 ==========
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-bb7e6c1015df4f6092ec1640c5632962")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

GITHUB_REPO = os.environ.get("REPO", "myjnathan/HelloCI")
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")
RUN_ID = os.environ.get("RUN_ID", "")

# ========================

def call_deepseek(prompt: str, system_prompt: Optional[str] = None) -> str:
    """调用 DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7
    }
    
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result["choices"][0]["message"]["content"]

def analyze_build_failure(error_log: str) -> Dict[str, Any]:
    """使用 DeepSeek 分析构建失败原因"""
    prompt = f"""
你是一个 C++ 专家和 CI/CD 工程师。以下是 GitHub Actions 构建失败的日志：

```
{error_log}
```

请分析：
1. 失败的根本原因
2. 具体的错误位置（文件、行号）
3. 修复建议（具体的代码修改）

请以 JSON 格式返回：
{{
    "cause": "原因描述",
    "location": "文件:行号 或 N/A",
    "fix_suggestion": "具体的修复代码或命令",
    "confidence": 0.0-1.0
}}
"""

    system_prompt = """你是一个专业的 C++ 工程师，擅长分析构建错误并提供精确的修复方案。
请只返回 JSON 格式，不要有其他内容。"""

    try:
        response = call_deepseek(prompt, system_prompt)
        # 尝试解析 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"⚠️ API 调用失败: {e}")
    
    return {
        "cause": "未知错误",
        "location": "N/A",
        "fix_suggestion": "请手动检查构建日志",
        "confidence": 0.0
    }

def get_failed_run_logs() -> str:
    """获取失败运行的日志"""
    if not GITHUB_TOKEN:
        # 尝试使用 gh CLI
        try:
            result = subprocess.run(
                ["gh", "run", "view", RUN_ID, "--log"],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout[-8000:] if result.stdout else ""
        except Exception as e:
            print(f"⚠️ 无法获取日志: {e}")
            return ""
    
    # 使用 GitHub API
    from github import Github
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    run = repo.get_workflow_run(int(RUN_ID))
    
    logs = ""
    for job in run.jobs():
        for log in job.logs():
            logs += log.text
    
    return logs[-8000:]

def create_fix_branch(fix_content: str, branch_name: str = "fix/ci-build") -> bool:
    """创建修复分支并提交"""
    if not GITHUB_TOKEN:
        print("⚠️ 未设置 GH_TOKEN，无法创建分支")
        return False
    
    try:
        # 使用 gh CLI 创建分支
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", f"Fix: CI build failure\n\n{fix_content}"], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        
        # 创建 PR
        subprocess.run([
            "gh", "pr", "create",
            "--title", "🤖 Auto Fix: CI Build Failure",
            "--body", f"自动修复 CI 构建失败\n\n修复内容:\n{fix_content}",
            "--base", "main"
        ], check=True)
        
        return True
    except Exception as e:
        print(f"⚠️ 创建 PR 失败: {e}")
        return False

def notify(message: str, level: str = "info"):
    """发送通知"""
    # 打印到日志
    emoji = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}.get(level, "📢")
    print(f"{emoji} {message}")
    
    # 可以扩展: Slack, Telegram, Discord 等

def main():
    print("=" * 50)
    print("🤖 CI Build Failure Agent 启动")
    print(f"📡 使用模型: {DEEPSEEK_MODEL}")
    print(f"📦 仓库: {GITHUB_REPO}")
    print(f"🔑 API Key: {DEEPSEEK_API_KEY[:10]}...")
    print("=" * 50)
    
    # 获取日志
    error_log = ""
    
    # 方法1: 从命令行参数读取文件
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            error_log = f.read()
    
    # 方法2: 从 stdin 读取 (GitHub Actions)
    if not error_log:
        try:
            error_log = sys.stdin.read()
        except:
            pass
    
    # 方法3: 从 GitHub API 获取
    if not error_log:
        error_log = get_failed_run_logs()
    
    if not error_log:
        notify("无法获取构建日志", "error")
        return 1
    
    # 截取关键部分
    if len(error_log) > 6000:
        error_log = error_log[-6000:]
    
    print(f"📋 获取到 {len(error_log)} 字符的日志")
    
    # 分析错误
    print("\n🔍 正在使用 DeepSeek 分析错误...")
    analysis = analyze_build_failure(error_log)
    
    print("\n" + "=" * 50)
    print("📊 分析结果:")
    print("=" * 50)
    print(f"  ❓ 原因: {analysis.get('cause', 'N/A')}")
    print(f"  📍 位置: {analysis.get('location', 'N/A')}")
    print(f"  🔧 修复建议: {analysis.get('fix_suggestion', 'N/A')}")
    print(f"  📈 置信度: {analysis.get('confidence', 0):.0%}")
    print("=" * 50)
    
    # 保存分析结果
    result = {
        "run_id": RUN_ID,
        "repo": GITHUB_REPO,
        "analysis": analysis,
        "timestamp": subprocess.run(
            ["date", "+%Y-%m-%d %H:%M:%S"],
            capture_output=True, text=True
        ).stdout.strip()
    }
    
    with open(os.environ.get("GITHUB_OUTPUT", "build_analysis.json"), "w") as f:
        json.dump(result, f, indent=2)
    
    # 根据置信度决定下一步
    confidence = analysis.get("confidence", 0)
    
    if confidence > 0.7:
        print(f"\n🔧 置信度高于 70%，尝试自动修复...")
        if create_fix_branch(analysis.get("fix_suggestion", "")):
            notify("✅ 自动修复 PR 已创建!", "success")
        else:
            notify("⚠️ 自动修复失败，请手动处理", "warning")
    else:
        notify(f"⚠️ 置信度较低 ({confidence:.0%})，跳过自动修复", "warning")
    
    print("\n✅ Agent 运行完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())