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
    或在 GitHub Actions 中通过文件传入日志
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
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API Error: {str(e)}"

def analyze_build_failure(error_log: str) -> Dict[str, Any]:
    """使用 DeepSeek 分析构建失败原因"""
    prompt = f"""
你是一个 C++ 专家和 CI/CD 工程师。以下是 GitHub Actions 构建失败的日志：

```
{error_log}
```

请分析：
1. 失败的根本原因是什么
2. 具体的错误位置（文件、行号、函数名）
3. 修复建议（具体的代码修改）

请以 JSON 格式返回：
{{
    "cause": "原因描述",
    "location": "文件:行号 或 N/A",
    "fix_suggestion": "具体的修复代码或命令",
    "confidence": 0.0-1.0
}}

只返回 JSON 格式，不要有其他内容。
"""

    system_prompt = "你是一个专业的 C++ 工程师，擅长分析构建错误并提供精确的修复方案。请只返回 JSON 格式。"

    try:
        response = call_deepseek(prompt, system_prompt)
        # 尝试解析 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"⚠️ 解析失败: {e}")
    
    return {
        "cause": "未知错误",
        "location": "N/A",
        "fix_suggestion": "请手动检查构建日志",
        "confidence": 0.0
    }

def get_github_run_logs() -> str:
    """从 GitHub API 获取运行日志"""
    if not GITHUB_TOKEN or not RUN_ID:
        return ""
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{RUN_ID}/logs"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        # 获取 jobs
        jobs_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{RUN_ID}/jobs"
        resp = requests.get(jobs_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return ""
        
        jobs_data = resp.json()
        logs = ""
        
        for job in jobs_data.get("jobs", []):
            logs += f"\n=== Job: {job['name']} ===\n"
            # 获取每个 step 的日志
            for step in job.get("steps", []):
                if step.get("conclusion") == "failure":
                    logs += f"Step: {step['name']} - FAILED\n"
        
        # 尝试获取构建日志
        build_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{RUN_ID}"
        resp = requests.get(build_url, headers=headers, timeout=30)
        if resp.status_code == 200:
            run_data = resp.json()
            # 获取 run 的 html_url
            logs += f"\nRun URL: {run_data.get('html_url', '')}\n"
        
        return logs
    except Exception as e:
        return f"Error fetching logs: {e}"

def create_fix_pr(fix_content: str, branch_name: str = "fix/ci-build") -> bool:
    """创建修复分支并提交 PR"""
    if not GITHUB_TOKEN:
        print("⚠️ 未设置 GH_TOKEN，无法创建 PR")
        return False
    
    try:
        # 使用 gh CLI
        # 创建分支
        subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
        subprocess.run(["git", "checkout", "-b", branch_name, "origin/main"], 
                      capture_output=True, check=True)
        subprocess.run(["git", "add", "-A"], capture_output=True, check=True)
        
        # 检查是否有更改
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not result.stdout.strip():
            print("没有需要修复的内容")
            return False
        
        subprocess.run(["git", "commit", "-m", f"🤖 Auto Fix: CI build failure\n\n{fix_content}"], 
                      capture_output=True, check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], 
                      capture_output=True, check=True)
        
        # 创建 PR
        result = subprocess.run([
            "gh", "pr", "create",
            "--title", "🤖 Auto Fix: CI Build Failure",
            "--body", f"自动修复 CI 构建失败\n\n修复内容:\n{fix_content}",
            "--base", "main"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ PR 已创建: {result.stdout}")
            return True
        else:
            print(f"⚠️ 创建 PR 失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️ 操作失败: {e}")
        return False

def notify(message: str, level: str = "info"):
    """发送通知"""
    emoji = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}.get(level, "📢")
    print(f"{emoji} {message}")

def main():
    print("=" * 60)
    print("🤖 CI Build Failure Agent 启动")
    print(f"📡 模型: {DEEPSEEK_MODEL}")
    print(f"📦 仓库: {GITHUB_REPO}")
    print(f"🔑 API: {DEEPSEEK_API_KEY[:10]}...")
    print("=" * 60)
    
    error_log = ""
    
    # 方法1: 从文件读取
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                error_log = f.read()
            print(f"📂 从文件读取: {log_file} ({len(error_log)} chars)")
    
    # 方法2: 从 GitHub API 获取
    if not error_log:
        print("🔄 从 GitHub API 获取日志...")
        error_log = get_github_run_logs()
        print(f"📡 获取到 {len(error_log)} 字符")
    
    if not error_log:
        notify("无法获取构建日志", "error")
        # 仍然尝试从环境变量获取
        error_log = os.environ.get("BUILD_LOG", "No logs available")
    
    # 截取关键部分
    if len(error_log) > 5000:
        error_log = error_log[-5000:]
    
    print(f"\n📋 分析 {len(error_log)} 字符的日志...")
    
    # 分析错误
    print("\n🔍 正在使用 DeepSeek 分析错误...")
    analysis = analyze_build_failure(error_log)
    
    print("\n" + "=" * 60)
    print("📊 分析结果:")
    print("=" * 60)
    print(f"  ❓ 原因: {analysis.get('cause', 'N/A')}")
    print(f"  📍 位置: {analysis.get('location', 'N/A')}")
    print(f"  🔧 修复: {analysis.get('fix_suggestion', 'N/A')}")
    print(f"  📈 置信度: {analysis.get('confidence', 0):.0%}")
    print("=" * 60)
    
    # 保存结果
    result = {
        "run_id": RUN_ID,
        "repo": GITHUB_REPO,
        "analysis": analysis
    }
    print(f"\n📝 结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 根据置信度决定下一步
    confidence = analysis.get("confidence", 0)
    
    if confidence > 0.7:
        print(f"\n🔧 置信度 {confidence:.0%} > 70%，尝试自动修复...")
        fix_content = analysis.get("fix_suggestion", "")
        if create_fix_pr(fix_content):
            notify("✅ 自动修复 PR 已创建!", "success")
        else:
            notify("⚠️ 自动修复失败", "warning")
    elif confidence > 0.5:
        notify(f"⚠️ 置信度 {confidence:.0%} 中等，跳过自动修复", "warning")
    else:
        notify(f"⚠️ 置信度 {confidence:.0%} 较低，请手动处理", "warning")
    
    print("\n✅ Agent 运行完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())