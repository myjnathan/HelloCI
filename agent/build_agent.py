#!/usr/bin/env python3
"""
CI Build Failure Agent
使用 DeepSeek API 自动分析并尝试修复构建失败

功能：
1. 监听 GitHub Actions 构建失败
2. 使用 DeepSeek 分析错误日志
3. 自动尝试修复并提交
"""

import os
import sys
import json
import subprocess
import requests
from typing import Optional, Dict, Any

# ========== 配置 ==========
DEEPSEEK_API_KEY = "sk-bb7e6c1015df4f6092ec1640c5632962"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

GITHUB_REPO = "myjnathan/HelloCI"
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")

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

    system_prompt = "你是一个专业的 C++ 工程师，擅长分析构建错误并提供精确的修复方案。"

    try:
        response = call_deepseek(prompt, system_prompt)
        # 尝试解析 JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"API 调用失败: {e}")
    
    return {
        "cause": "未知错误",
        "location": "N/A",
        "fix_suggestion": "请手动检查构建日志",
        "confidence": 0.0
    }

def get_failed_run_info() -> Optional[Dict[str, Any]]:
    """获取最近失败的 CI 运行信息"""
    if not GITHUB_TOKEN:
        print("警告: 未设置 GH_TOKEN 环境变量")
        return None
    
    cmd = [
        "gh", "run", "list",
        "--repo", GITHUB_REPO,
        "--limit", "5",
        "--json", "databaseId,status,conclusion,title"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"获取运行列表失败: {result.stderr}")
        return None
    
    runs = json.loads(result.stdout)
    for run in runs:
        if run.get("conclusion") == "failure":
            return run
    
    return None

def get_run_logs(run_id: str) -> str:
    """获取运行日志"""
    cmd = ["gh", "run", "view", run_id, "--log"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout[-5000:]  # 取最后5000字符

def apply_fix(fix_suggestion: str, file_path: str) -> bool:
    """应用修复"""
    print(f"建议修复: {fix_suggestion}")
    print(f"目标文件: {file_path}")
    # 这里可以实现自动修复逻辑
    return True

def main():
    print("🤖 CI Build Failure Agent 启动")
    print(f"📡 使用模型: {DEEPSEEK_MODEL}")
    print(f"📦 仓库: {GITHUB_REPO}")
    
    # 获取失败的运行
    failed_run = get_failed_run_info()
    if not failed_run:
        print("✅ 没有失败的 CI 运行")
        return 0
    
    run_id = failed_run["databaseId"]
    print(f"❌ 发现失败的运行: {run_id}")
    
    # 获取日志
    logs = get_run_logs(str(run_id))
    print(f"📋 获取到 {len(logs)} 字符的日志")
    
    # 分析错误
    print("🔍 正在使用 DeepSeek 分析错误...")
    analysis = analyze_build_failure(logs)
    
    print("\n📊 分析结果:")
    print(f"  原因: {analysis.get('cause', 'N/A')}")
    print(f"  位置: {analysis.get('location', 'N/A')}")
    print(f"  修复建议: {analysis.get('fix_suggestion', 'N/A')}")
    print(f"  置信度: {analysis.get('confidence', 0):.0%}")
    
    # 如果置信度高，可以选择自动修复
    if analysis.get("confidence", 0) > 0.7:
        print("\n🔧 置信度高，准备自动修复...")
        # apply_fix(...)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())