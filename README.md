# HelloCI - C++ CI/CD 示例项目

![CI Status](https://github.com/myjnathan/HelloCI/actions/workflows/ci.yml/badge.svg)
![GitHub stars](https://img.shields.io/github/stars/myjnathan/HelloCI)
![GitHub forks](https://img.shields.io/github/forks/myjnathan/HelloCI)

一个完整的 C++ 项目，包含 GitHub Actions CI/CD 流程和自动修复 Agent。

## 📁 项目结构

```
HelloCI/
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI/CD 配置
├── agent/
│   ├── build_agent.py      # DeepSeek API 驱动的自动修复 Agent
│   └── README.md           # Agent 使用说明
├── include/
│   └── calculator.h       # 计算器头文件
├── src/
│   ├── main.cpp           # 主程序
│   └── calculator.cpp     # 计算器实现
├── CMakeLists.txt         # CMake 构建配置
├── TUTORIAL.md            # 完整教程
├── README.md              # 本文件
└── .gitignore
```

## 🚀 功能特性

- ✅ **自动化 CI/CD**: 每次推送自动构建、测试
- ✅ **单元测试**: 使用 CTest 进行测试
- 🤖 **智能 Agent**: 构建失败时自动分析并尝试修复
- 📊 **DeepSeek AI**: 使用 DeepSeek LLM 分析错误

## 🛠️ 快速开始

### 本地构建

```bash
# 克隆项目
git clone https://github.com/myjnathan/HelloCI.git
cd HelloCI

# 创建 build 目录并配置
cmake -B build

# 编译
cmake --build build

# 运行测试
cd build && ctest --output-on-failure

# 运行程序
./build/hello_ci
```

### CI/CD 流程

1. 每次推送到 `main` 分支自动触发
2. 安装依赖 (CMake, g++)
3. 配置并编译项目
4. 运行单元测试
5. 执行应用程序

## 🤖 Agent 自动修复

### 工作流程

```
推送代码 → CI 构建失败 → Agent 自动触发
    ↓
使用 DeepSeek 分析错误日志
    ↓
置信度 > 70%? → 自动创建修复 PR
    ↓
审核并合并 PR
```

### 配置 Secrets

在 GitHub 仓库设置中添加：

| Secret | 值 |
|--------|-----|
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |
| `GH_TOKEN` | GitHub PAT (需要 repo 权限) |

### 测试 Agent

```bash
# 本地测试
pip install requests PyGithub
export GH_TOKEN="your_token"
export DEEPSEEK_API_KEY="your_key"
python agent/build_agent.py error.log
```

## 📖 文档

- [完整教程](./TUTORIAL.md) - 从零开始学习 CI/CD
- [Agent 说明](./agent/README.md) - 了解 Agent 工作原理

## 🔧 常见问题

**Q: 构建失败怎么办？**
A: Agent 会自动分析并尝试创建修复 PR。如果没有自动修复，请查看 CI 日志手动处理。

**Q: 如何添加新的测试？**
A: 在 `CMakeLists.txt` 中添加 `add_test()` 条目。

**Q: 如何修改 CI 配置？**
A: 编辑 `.github/workflows/ci.yml`。

## 📝 License

MIT License

## 👤 作者

- GitHub: [@myjnathan](https://github.com/myjnathan)

---

⭐ 如果对你有帮助，欢迎 star！