# GitHub Copilot 多Agent协作 Demo

本项目演示了 GitHub Copilot **Custom Agent** 的多Agent协作模式，通过 Handoff 机制实现 **诗人Agent** 和 **诗歌编辑Agent** 的无缝协作。

## 📂 项目结构

```text
.github/
└── agents/
    ├── poet.agent.md            # 诗人Agent（含 Handoff 配置）
    └── poetry-editor.agent.md   # 诗歌编辑Agent
```

## 🤖 Agent 说明

### 1. 诗人Agent (`#poet`)

| 项目     | 说明                                          |
|----------|-----------------------------------------------|
| 文件     | `.github/agents/poet.agent.md`                |
| 职责     | 接收用户输入，创作诗歌，判断是否需要配图      |
| Handoff  | 创作完成后通过 Handoff 按钮交给诗歌编辑Agent  |
| 可用工具 | `agent`, `search`, `fetch`                    |

**核心功能：**
- 根据用户主题/情感/场景创作诗歌
- 自动识别适合的诗歌风格（古体诗、现代诗、词、赋等）
- 判断是否需要为诗歌生成配图
- 通过 Handoff 将作品传递给诗歌编辑Agent

### 2. 诗歌编辑Agent (`#poetry-editor`)

| 项目     | 说明                                          |
|----------|-----------------------------------------------|
| 文件     | `.github/agents/poetry-editor.agent.md`       |
| 职责     | 审阅诗人Agent的作品，进行润色和最终定稿        |
| 输入     | 来自诗人Agent的 Handoff 或用户直接输入         |
| 可用工具 | `search`, `fetch`                             |

**核心功能：**
- 格律审查（平仄、韵脚、对仗）
- 用词润色和意境优化
- 风格一致性检查
- 输出专业的编辑报告和最终定稿

## 🔄 协作流程（Handoff 机制）

```text
用户输入 → 诗人Agent → [创作诗歌] → 点击 Handoff 按钮 → 诗歌编辑Agent → [审阅润色] → 最终输出
                ↓                   「交给诗歌编辑润色」
          判断是否需要配图
```

> **Handoff 说明**：诗人Agent 完成创作后，聊天界面底部会出现 **「交给诗歌编辑润色」** 按钮。
> 点击后会自动切换到诗歌编辑Agent，并预填审阅润色的提示词。

## 🚀 使用方法

### 前提条件
- VS Code（最新版本）
- GitHub Copilot 扩展（已启用）

### 使用步骤

1. **打开 VS Code**，在本项目目录中工作

2. **切换到诗人Agent**：在 Copilot Chat 的 Agent 下拉菜单中选择 **poet**，然后输入创作需求

   ```text
   写一首关于秋天落叶的诗
   ```

3. **诗人Agent** 创作完成后，聊天界面底部会出现 **「交给诗歌编辑润色」** 的 Handoff 按钮

4. **点击 Handoff 按钮**：自动切换到 **poetry-editor** Agent，并预填润色提示词

5. **查看最终输出**：诗歌编辑Agent 会输出完整的编辑报告和润色后的最终版本

### 示例对话

```text
👤 用户（poet Agent）：写一首描写西湖月色的诗，需要配图

🤖 诗人Agent：
📜 【西湖月色】
银盘初上柳梢头，碧水长天共一秋。
断桥残雪今何在，独倚栏杆看月游。
...

                    [ 交给诗歌编辑润色 ]  ← Handoff 按钮

👤 用户点击 Handoff 按钮 → 自动切换到 poetry-editor Agent

🤖 诗歌编辑Agent：
═══════════════════════
📖 诗歌编辑报告
✨ 最终定稿：...
═══════════════════════
```

## 📝 自定义扩展

你可以基于此模板扩展更多Agent：

- **书法Agent**：为诗歌选择合适的书法字体和排版
- **配图Agent**：根据诗歌内容生成AI配图
- **翻译Agent**：将诗歌翻译为其他语言
- **朗诵Agent**：为诗歌添加朗诵标注和节奏指导

## License

MIT
