# C++ 项目 CI/CD 完整教程

本教程将帮助你从零开始搭建一个完整的 C++ CI/CD 流程。

---

## 环境要求

- macOS / Linux / Windows (WSL)
- CMake >= 3.10
- Git
- GitHub 账号

---

## 第一步：本地开发环境准备

### macOS

```bash
# 使用 Homebrew 安装
brew install cmake

# 验证安装
cmake --version
# 输出类似: cmake version 3.28.1
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y cmake g++
cmake --version
```

### CentOS/RHEL

```bash
sudo yum install cmake gcc-c++
cmake --version
```

---

## 第二步：创建项目结构

```bash
# 创建项目目录
mkdir -p HelloCI/src HelloCI/include HelloCI/.github/workflows

# 目录结构
HelloCI/
├── include/          # 头文件目录
├── src/              # 源代码目录
├── .github/
│   └── workflows/    # CI/CD 配置目录
├── CMakeLists.txt    # CMake 构建配置
└── README.md         # 项目说明
```

---

## 第三步：编写代码文件

### 头文件 (include/calculator.h)

```cpp
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    int add(int a, int b);
    int subtract(int a, int b);
    int multiply(int a, int b);
    int divide(int a, int b);
};

#endif // CALCULATOR_H
```

### 源文件 (src/calculator.cpp)

```cpp
#include "calculator.h"

int Calculator::add(int a, int b) {
    return a + b;
}

int Calculator::subtract(int a, int b) {
    return a - b;
}

int Calculator::multiply(int a, int b) {
    return a * b;
}

int Calculator::divide(int a, int b) {
    if (b == 0) {
        return 0;  // 简单的错误处理
    }
    return a / b;
}
```

### 主程序 (src/main.cpp)

```cpp
#include <iostream>
#include "calculator.h"

int main() {
    Calculator calc;
    
    std::cout << "=== Simple Calculator ===" << std::endl;
    std::cout << "5 + 3 = " << calc.add(5, 3) << std::endl;
    std::cout << "10 - 4 = " << calc.subtract(10, 4) << std::endl;
    std::cout << "6 * 7 = " << calc.multiply(6, 7) << std::endl;
    std::cout << "20 / 4 = " << calc.divide(20, 4) << std::endl;
    std::cout << "10 / 0 = " << calc.divide(10, 0) << " (expected: 0)" << std::endl;
    
    return 0;
}
```

---

## 第四步：配置 CMake 构建

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.10)

# 重要：enable_testing() 必须在 project() 之前
enable_testing()

project(HelloCI VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

add_executable(hello_ci 
    src/main.cpp
    src/calculator.cpp
)

# 添加测试
add_test(NAME basic_test COMMAND ${CMAKE_CURRENT_BINARY_DIR}/hello_ci)
```

### 本地构建测试

```bash
# 进入项目目录
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

预期输出：
```
=== Simple Calculator ===
5 + 3 = 8
10 - 4 = 6
6 * 7 = 42
20 / 4 = 5
10 / 0 = 0 (expected: 0)
```

---

## 第五步：配置 GitHub Actions CI/CD

### .github/workflows/ci.yml

```yaml
name: C++ CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake g++
        
    - name: Configure
      run: cmake -B build -DCMAKE_BUILD_TYPE=Release
      
    - name: Build
      run: cmake --build build
      
    - name: Run tests
      working-directory: build
      run: ctest --output-on-failure
      
    - name: Run application
      run: ./build/hello_ci
```

**配置说明：**
- `on push`: 当推送到 main 分支时触发
- `on pull_request`: 当创建 PR 时触发
- `runs-on: ubuntu-latest`: 使用 GitHub 托管的 Ubuntu 运行器

---

## 第六步：初始化 Git 并推送到 GitHub

### 配置 Git

```bash
# 配置用户名和邮箱
git config --global user.email "your-email@example.com"
git config --global user.name "your-username"
```

### 创建 .gitignore

```
build/
*.o
*.exe
*.out
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
Makefile
*.swp
*.swo
.DS_Store
```

### 初始化并推送

```bash
# 初始化 Git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: C++ project with CI/CD"

# 创建 GitHub 仓库并推送
gh repo create HelloCI --public --source=. --push
```

### 验证 CI/CD

推送后，前往 `https://github.com/your-username/HelloCI/actions` 查看 CI 运行状态。

---

## 常见问题 FAQ

### Q1: 测试显示 "No tests were found" 怎么办？

**原因：** `enable_testing()` 放置位置不正确

**解决：** 确保 `enable_testing()` 在 `project()` 之前：

```cmake
cmake_minimum_required(VERSION 3.10)
enable_testing()  # 必须在这里
project(HelloCI VERSION 1.0.0 LANGUAGES CXX)
# ... 其他配置
```

### Q2: 国内访问 GitHub 慢或推送失败怎么办？

**方法一：设置代理**

```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

**方法二：使用 GitHub CLI**

```bash
gh auth login
```

### Q3: 如何查看 CI 运行日志？

```bash
# 查看最近的运行
gh run list

# 查看具体运行详情
gh run view <run-id>

# 查看失败日志
gh run view <run-id> --log-failed
```

或者访问：`https://github.com/用户名/仓库名/actions/runs/运行ID`

### Q4: 如何本地测试 CI 流程？

```bash
# 完整的本地 CI 测试
cmake -B build
cmake --build build
cd build && ctest --output-on-failure
./hello_ci
```

### Q5: 如何触发 CI？

- 推送代码到 main 分支：`git push origin main`
- 创建或更新 Pull Request
- 修改 `.github/workflows/ci.yml` 文件

### Q6: CMake 版本太旧怎么办？

**macOS:**
```bash
brew upgrade cmake
```

**Ubuntu:**
```bash
sudo apt-get install cmake3
# 或下载最新版本
wget https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-linux-x86_64.sh
```

### Q7: CI 构建失败怎么办？

1. 查看 CI 日志确定错误原因
2. 本地修复问题
3. 提交并推送修复

**提示：** 可以使用 Agent 自动处理构建失败，详见 Agent 相关文档。

**提示：** 可以使用 Agent 自动处理构建失败，详见第七部分。

### Q8: 如何添加更多测试？

在 CMakeLists.txt 中添加更多测试：

```cmake
add_test(NAME test_add COMMAND ${CMAKE_CURRENT_BINARY_DIR}/hello_ci)
add_test(NAME test_subtract COMMAND ${CMAKE_CURRENT_BINARY_DIR}/hello_ci)
```

或者使用 Google Test、Catch2 等测试框架。

### Q9: 如何使用其他 CI 平台？

- **GitLab CI**: 创建 `.gitlab-ci.yml`
- **Jenkins**: 配置 Jenkinsfile
- **CircleCI**: 创建 `.circleci/config.yml`

### Q10: 如何设置 CI 定时运行？

在 workflow 中添加 schedule 触发器：

```yaml
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 每天午夜运行
```

---

## 第七步：配置自动修复 Agent (可选)

本节介绍如何配置一个使用 DeepSeek API 的自动修复 Agent，当 CI 构建失败时自动分析并尝试修复。

### 7.1 Agent 功能介绍

🤖 **CI Build Failure Agent** 可以：
- 自动检测 CI 构建失败
- 使用 DeepSeek AI 分析错误日志
- 提供具体的修复建议
- 自动创建修复 PR（可选）

### 7.2 配置 GitHub Secrets

在 GitHub 仓库中添加以下 Secrets：

1. 打开 `https://github.com/你的用户名/HelloCI/settings/secrets/actions`
2. 点击 "New repository secret"

| Secret 名称 | 值 | 说明 |
|-------------|-----|------|
| `DEEPSEEK_API_KEY` | `sk-bb7e6c1015df4f6092ec1640c5632962` | DeepSeek API 密钥 |
| `GH_TOKEN` | 你的 GitHub PAT | 需要 repo 权限的 Token |

**创建 GH_TOKEN:**
```bash
# 使用 gh CLI 创建
gh auth token
# 或在 GitHub 设置中创建: Settings → Developer settings → Personal access tokens
```

### 7.3 Agent 工作流程

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  CI Build   │────▶│  Agent       │────▶│  DeepSeek  │
│  Fails      │     │  Detects     │     │  Analysis  │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                    ┌──────────────┐            │
                    │  Confidence  │◀───────────┘
                    │  Check       │
                    └──────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐       ┌───────────┐      ┌──────────┐
   │ > 70%   │       │  50-70%   │      │  < 50%   │
   │ Auto Fix│       │  Notify   │      │  Manual  │
   │ + PR    │       │  Only     │      │  Review  │
   └─────────┘       └───────────┘      └──────────┘
```

### 7.4 本地测试 Agent

```bash
# 安装依赖
pip install requests PyGithub

# 运行 Agent (需要 GH_TOKEN 环境变量)
export GH_TOKEN="your_github_token"
export DEEPSEEK_API_KEY="sk-bb7e6c1015df4f6092ec1640c5632962"
export RUN_ID="1234567890"
export REPO="your-username/HelloCI"

python agent/build_agent.py
```

### 7.5 CI 集成 Agent

Agent 已集成到 `.github/workflows/ci.yml` 中：

```yaml
# 构建失败后自动触发 Agent
agent:
  needs: build
  if: ${{ failure() }}
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install requests PyGithub
    - name: Run Build Failure Agent
      env:
        DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
      run: python agent/build_agent.py
```

### 7.6 Agent 代码说明

核心文件: `agent/build_agent.py`

| 函数 | 功能 |
|------|------|
| `call_deepseek()` | 调用 DeepSeek API 分析错误 |
| `analyze_build_failure()` | 解析日志并生成修复建议 |
| `create_fix_branch()` | 自动创建修复分支和 PR |
| `notify()` | 发送通知（可扩展） |

### 7.7 常见问题 FAQ (Agent)

**Q1: Agent 分析不准确怎么办？**

**解决：** 
- 调整 `temperature` 参数（当前 0.7）
- 优化 system prompt
- 提供更多上下文日志

**Q2: API 调用失败**

**检查：**
- API Key 是否正确
- 网络是否可达
- API 配额是否用完

**Q3: 自动修复 PR 创建失败**

**原因：** GH_TOKEN 权限不足
**解决：** 确保 Token 有以下权限：
- `repo` (完整仓库访问)
- `workflow` (工作流访问)

**Q4: 如何关闭自动修复功能？**

修改 `agent/build_agent.py` 中的置信度阈值：
```python
if confidence > 0.7:  # 改为更高如 0.9 或直接设为 1.0
```

---

## 扩展内容

### 添加代码格式化检查

```yaml
- name: Check code format
  run: |
    sudo apt-get install -y clang-format
    clang-format --dry-run -Werror src/*.cpp
```

### 添加静态分析

```yaml
- name: Static analysis
  run: |
    sudo apt-get install -y cppcheck
    cppcheck --enable=all src/
```

### 添加构建矩阵测试

```yaml
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        compiler: [g++, clang++]
```

---

## 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [CMake 官方文档](https://cmake.org/documentation/)
- [C++ 最佳实践](https://github.com/cpp-best-practices/cppbestpractices)

---

*本教程由 AI 助手生成*