# CI Build Failure Agent

使用 DeepSeek API 自动分析并尝试修复 GitHub Actions 构建失败。

## 功能

- 🤖 **自动分析**: 使用 DeepSeek LLM 分析构建失败原因
- 📊 **智能诊断**: 识别错误位置并提供修复建议
- 🔧 **自动修复**: 可配置的自动修复功能
- 📢 **消息通知**: 支持多种渠道通知 (Slack, Discord, Telegram 等)

## 配置

### 1. 环境变量

```bash
# 必需
export DEEPSEEK_API_KEY="sk-bb7e6c1015df4f6092ec1640c5632962"

# 可选
export GH_TOKEN="your_github_token"  # 用于获取 CI 日志
export OPENCLAW_CHANNEL="webchat"     # 通知渠道
```

### 2. API 配置

| 配置项 | 值 |
|--------|-----|
| API URL | https://api.deepseek.com/v1/chat/completions |
| 模型 | deepseek-chat |
| API Key | sk-bb7e6c1015df4f6092ec1640c5632962 |

## 使用方法

### 本地运行

```bash
# 安装依赖
pip install requests

# 运行 Agent
python agent/build_agent.py
```

### 在 GitHub Actions 中集成

创建 `.github/workflows/agent.yml`:

```yaml
name: CI Failure Analysis Agent

on:
  workflow_run:
    workflows: ["C++ CI/CD Pipeline"]
    types: [completed]
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Run Build Failure Agent
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
        run: |
          pip install requests
          python agent/build_agent.py
      
      - name: Create Fix PR (if needed)
        if: failure()
        run: |
          # 自动创建修复 PR 的逻辑
          echo "Creating fix PR..."
```

### 配置 GitHub Secrets

1. 打开 GitHub 仓库设置
2. → Secrets and variables → Actions
3. 添加:
   - `DEEPSEEK_API_KEY`: 你的 DeepSeek API Key
   - `GH_TOKEN`: GitHub Personal Access Token (需要 repo 权限)

## 工作流程

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  CI Build   │────▶│  Agent       │────▶│  Analysis  │
│  Fails      │     │  Detects     │     │  Result    │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                    ┌──────────────┐            │
                    │  Auto Fix    │◀───────────┘
                    │  (optional)  │
                    └──────────────┘
                           │
                    ┌──────────────┐
                    │  Create PR   │
                    │  + Notify    │
                    └──────────────┘
```

## Agent 可自动处理的场景

| 场景 | Agent 行为 |
|------|-----------|
| **编译错误** | 分析错误，提供修复代码 |
| **测试失败** | 分析失败原因，建议修复 |
| **链接错误** | 识别缺失的库/头文件 |
| **CMake 配置错误** | 提供正确的 CMake 配置 |

## API 说明

### analyze_build_failure(error_log: str) -> dict

分析构建失败日志。

返回:
```json
{
    "cause": "缺少 CMake 模块",
    "location": "CMakeLists.txt:16",
    "fix_suggestion": "添加 enable_testing() 在 project() 之前",
    "confidence": 0.85
}
```

## 扩展

### 添加更多通知渠道

在 `build_agent.py` 中添加:

```python
def notify_slack(message: str):
    """发送 Slack 通知"""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={"text": message})

def notify_telegram(message: str):
    """发送 Telegram 通知"""
    # 使用 OpenClaw 的 message 工具
    pass
```

### 添加自动修复 PR

```python
def create_fix_pr(fix_content: str, branch_name: str = "fix/ci-build"):
    """自动创建修复 PR"""
    # 1. 创建分支
    # 2. 应用修复
    # 3. 提交并推送
    # 4. 创建 PR
    pass
```

## 故障排除

### Q: API 调用失败

**检查:**
1. API Key 是否正确
2. 网络是否可达
3. API 配额是否用完

### Q: 无法获取 CI 日志

**解决:**
1. 设置 `GH_TOKEN` 环境变量
2. 确保 Token 有 `repo` 权限

### Q: 分析结果不准确

**优化:**
1. 提供更多上下文日志
2. 调整 `temperature` 参数
3. 优化 system prompt

## 相关文件

- `agent/build_agent.py` - Agent 主程序
- `.github/workflows/ci.yml` - CI/CD 流程
- `TUTORIAL.md` - 完整教程