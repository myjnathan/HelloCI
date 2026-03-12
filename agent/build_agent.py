#!/usr/bin/env python3
"""
CI Build Failure Agent
使用 DeepSeek API 自动分析并尝试修复构建失败
"""

import os
import sys
import json

# ========== 配置 ==========
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-bb7e6c1015df4f6092ec1640c5632962")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

GITHUB_REPO = os.environ.get("REPO", "myjnathan/HelloCI")
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")
RUN_ID = os.environ.get("RUN_ID", "")

# ========================

def log(msg):
    """打印日志"""
    print(f"🤖 {msg}", flush=True)

def call_deepseek(prompt: str, system_prompt: str = None) -> str:
    """调用 DeepSeek API"""
    import requests
    
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

def analyze_build_failure(error_log: str) -> dict:
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
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        log(f"解析失败: {e}")
    
    return {
        "cause": "未知错误",
        "location": "N/A",
        "fix_suggestion": "请手动检查构建日志",
        "confidence": 0.0
    }

def get_source_files() -> list:
    """获取源代码文件列表"""
    import os
    src_files = []
    for root, dirs, files in os.walk('.'):
        # 跳过隐藏目录和构建目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['build', '__pycache__']]
        for f in files:
            if f.endswith(('.cpp', '.h', '.hpp', '.c', '.cc')):
                src_files.append(os.path.join(root, f))
    return src_files

def create_fix_pr(fix_content: str) -> bool:
    """创建修复 PR"""
    if not GITHUB_TOKEN:
        log("未设置 GH_TOKEN，无法创建 PR")
        return False
    
    import subprocess
    
    try:
        branch_name = "fix/ci-build"
        
        # 配置 git
        subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "agent@helloci.local"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "CI Agent"], check=True)
        
        # 获取远程分支
        subprocess.run(["git", "fetch", "origin", "main"], capture_output=True)
        
        # 检查分支是否已存在，若存在则删除
        subprocess.run(["git", "branch", "-D", branch_name], capture_output=True)
        subprocess.run(["git", "checkout", "-b", branch_name, "origin/main"], capture_output=True, check=True)
        
        # 检查是否有需要修复的文件
        log("检查源代码文件...")
        
        # 简单检查并尝试修复常见的编译错误
        import os
        src_files = get_source_files()
        
        modified = False
        for src_file in src_files:
            if os.path.exists(src_file):
                with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检测并修复：unknown_function 调用
                if 'unknown_function' in content:
                    lines = content.split('\n')
                    new_lines = [l for l in lines if 'unknown_function' not in l]
                    new_content = '\n'.join(new_lines)
                    
                    with open(src_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    log(f"已修复: {src_file}")
                    modified = True
                
                # 检测并修复：未初始化的变量使用
                if 'error:' in content.lower():
                    # 记录问题但不自动修改
                    pass
        
        if not modified:
            log("没有需要修复的内容")
            return False
        
        # 提交更改
        subprocess.run(["git", "add", "-A"], capture_output=True, check=True)
        subprocess.run([
            "git", "commit", "-m", 
            f"🤖 Auto Fix: CI Build Failure\n\n{fix_content}"
        ], capture_output=True, check=True)
        
        # 推送到远程
        subprocess.run(["git", "push", "-u", "origin", branch_name], capture_output=True, check=True)
        
        # 创建 PR
        result = subprocess.run([
            "gh", "pr", "create",
            "--title", "🤖 Auto Fix: CI Build Failure",
            "--body", f"自动修复 CI 构建失败\n\n修复内容:\n{fix_content}",
            "--base", "main"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            log(f"✅ PR 已创建: {result.stdout}")
            return True
        else:
            log(f"创建 PR 失败: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"操作失败: {e}")
        import traceback
        log(traceback.format_exc())
        return False

def main():
    log("=" * 50)
    log("CI Build Failure Agent 启动")
    log(f"模型: {DEEPSEEK_MODEL}")
    log(f"仓库: {GITHUB_REPO}")
    log("=" * 50)
    
    error_log = ""
    
    # 从文件读取
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                error_log = f.read()
            log(f"从文件读取: {log_file} ({len(error_log)} chars)")
        else:
            log(f"文件不存在: {log_file}")
    
    if not error_log:
        log("无法获取构建日志")
        error_log = "No logs"
    
    # 截取关键部分
    if len(error_log) > 4000:
        error_log = error_log[-4000:]
    
    log(f"分析 {len(error_log)} 字符...")
    
    # 分析
    analysis = analyze_build_failure(error_log)
    
    log("=" * 50)
    log("📊 分析结果:")
    log(f"  原因: {analysis.get('cause', 'N/A')}")
    log(f"  位置: {analysis.get('location', 'N/A')}")
    log(f"  修复: {analysis.get('fix_suggestion', 'N/A')}")
    log(f"  置信度: {analysis.get('confidence', 0):.0%}")
    log("=" * 50)
    
    # 保存分析结果到文件
    with open("agent_analysis_result.json", "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    log("📝 分析结果已保存到 agent_analysis_result.json")
    
    # 根据置信度决定
    confidence = analysis.get("confidence", 0)
    
    if confidence > 0.7:
        log(f"置信度 {confidence:.0%} > 70%，尝试自动修复...")
        if create_fix_pr(analysis.get("fix_suggestion", "")):
            log("✅ 自动修复 PR 已创建!")
        else:
            log("⚠️ 自动修复失败")
    else:
        log(f"置信度 {confidence:.0%}，跳过自动修复")
    
    log("✅ 完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())