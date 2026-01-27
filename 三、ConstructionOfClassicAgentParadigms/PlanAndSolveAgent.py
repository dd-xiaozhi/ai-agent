import ast

from LLMClient import LLMClient

PLANNER_PROMPT_TEMPLATE = """
    你是一个顶级的 AI 规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
    请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
    你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

    问题: {question}

    请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
    ```python
    ["步骤1", "步骤2", "步骤3", ...]
    ```
    """


class Planner:
    def __init__(self):
        self.llmClient = LLMClient(model="deepseek-chat")

    def plan(self, question):
        """
        根据用户的问题生成执行计划
        :param question: 问题
        :return: 执行计划
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        message = [
            { "role": "user", "content": prompt }
        ]

        print("====================== LLM正在生成执行计划... ======================")

        response_txt = self.llmClient.generate(message=message) or ""
        print(f"✅ 计划已生成:\n{response_txt}")

        # 解析模型输出
        try:
            plan_str = response_txt.split("```python")[1].split("```")[0].strip()
            # 使用 ast.literal_eval 解析字符串为 Python List 对象
            plan_list = ast.literal_eval(plan_str)
            return plan_list if isinstance(plan_list, list) else []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []


def main():
    pass

if __name__ == '__main__':
    main()
