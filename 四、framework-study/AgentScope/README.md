# 三国狼人杀 Demo (基于 AgentScope)

这是一个基于 AgentScope 框架实现的“三国狼人杀”游戏 Demo。

## 简介
本 Demo 演示了如何使用 AgentScope 构建一个多智能体游戏。我们将狼人杀的角色映射到了三国人物上：

- **狼人 (Werewolf)**: 曹操 (Cao Cao), 司马懿 (Sima Yi)
- **平民 (Villager)**: 刘备 (Liu Bei), 孙权 (Sun Quan)
- **预言家 (Seer)**: 诸葛亮 (Zhuge Liang)
- **女巫 (Witch)**: 貂蝉 (Diao Chan)

## 运行方法

1.  确保已安装 `agentscope`：
    ```bash
    pip install agentscope
    ```

2.  设置 OpenAI API Key：
    在 `three_kingdoms_werewolf.py` 中填入你的 API Key，或者设置环境变量：
    ```bash
    export OPENAI_API_KEY="your-api-key"
    ```

3.  运行脚本：
    ```bash
    python three_kingdoms_werewolf.py
    ```

## 实现细节
- 使用 `DictDialogAgent` 实现结构化输出（JSON）。
- 使用 `msghub` 实现群聊（狼人讨论、白天讨论）。
- 包含基本的黑夜/白天流程模拟。
