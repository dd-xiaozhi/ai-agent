# 二、快速入门

我们来快速搭建一个旅游规划的 agent，让这个 agent 来帮客户规划某个城市的旅游行程推荐







## 1 封装兼容 OpenAI 客户端

通过 OpenAI 来兼容各种大模型，同时封装简化调用方法

```PY
class OpenAICompatibleClient:
    """
    OpenAI兼容客户端, 用于与OpenAI API兼容
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        生成文本

        :param prompt: 用户提示词
        :param system_prompt: 系统提示词
        :return 生成的文本
        """
        print(f"Generating text with model: {self.model}")
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )

            answer = response.choices[0].message.content
            print(f"Generated answer: \n{answer}")
            return answer
        except Exception as e:
            return f'错误: 调用OpenAI API失败: {e}'
```





## 2 添加工具函数

添加agent所需要的工具函数，以备后面agent使用

```py
def get_weather(city: str) -> str:
    """
    获取天气
        Args:
            city: 城市名称
        Returns:
            str: 天气信息
    """

    url = f"https://wttr.in/{city}?format=j1"
    try:
        # 发起请求
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # 解析数据
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        return f'{city}当前天气：{weather_desc}, 气温：{temp_c} 摄氏度'
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气遇到网络问题: {e}"

    except (KeyError, IndexError) as e:
        return f'错误：解析天气数据失败：{e}'


def get_attraction(city: str, weather: str) -> str:
    """
    获取旅游景点
        Args:
            city: 城市名称
            weather: 天气信息
        Returns:
            str: 旅游景点信息
    """
    # 初始化客户端
    tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

    query = f"'{city}' 在 '{weather}' 天气下值得去的旅游景点以及推荐理由"

    try:
        response = tavily.search(query=query, search_depth='basic', include_answer=True)

        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到可推荐的景点"

        return "根据搜索，为您找到以下信息：\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行搜索时遇到网络问题: {e}"


available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction
}
```





## 3 循环执行观测结束

我们会使用 ReAct(Reasoning + Acting) 模式，这是一种推理+执行的循环机制，让大模型来自主推断下一步的行动，直至任务需求完成。

在系统提示词中定义大模型的角色定义以及角色行为和模型输出格式，通过解析模型的输出来判断需要执行工具调用还是结束循环。

```python
def main():
    AGENT_SYSTEM_PROMPT = """
    你是一个旅行智能助手。你的任务是分析用户需求，使用合适的工具一步步解决用户提取的需求。

    # 可用工具
    - `get_weather(city: str)`: 查询指定城市的实时天气。
    - `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

    # 行动模式：
    首先是你的思考过程，然后是你要执行的具体行动，每次回复只输出一对 Thought 和 Action（必须输出一对），如果某一步重试三次后再遇到问题则报错结束，报错信息由你定义。
    你的回答必须严格遵守以下格式：
    Thought:[这里是你的思考过程和下一步计划]
    Action:[这里是你要调用的工具，格式为：function_name(arg_name='arg_value')]

    # 任务完成
    当你收集到足够多的信息，能够回答用户问题时，你必须在 `Action` 字段后使用 `finish(answer="....")` 来输出最终答案，以 markdown 的形式输出


    请开始吧！

    """

    client = OpenAICompatibleClient(
        model="deepseek-chat",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL")
    )

    user_prompt = "帮我查询今天广州的天气，根据今天的天气推荐几个合适的旅游景点，输出要详细"
    prompt_history = [f'用户请求: {user_prompt}']

    print(f"用户输入: {user_prompt}\n" + "=" * 40)

    # 运行主循环
    for i in range(10):
        print(f"--- 第{i + 1}轮思考 ---")

        full_prompt = "\n".join(prompt_history)
        llm_output = client.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        # 模型可能会输出多余的 Thought-Action,需要截断
        match = re.search(r'(Thought:\s*.*?Action:\s*.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',
                          llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print(f"截断后的输出: {llm_output}")
        print(f"LLM输出: \n{llm_output}")
        prompt_history.append(llm_output)

        action_match = re.search(r"Action:\s*(.*)", llm_output, re.DOTALL)
        if not action_match:
            print("解析错误：模型输出未找到 Action")
            break

        action_str = action_match.group(1).strip()

        if action_str.startswith("finish"):
            final_answer = re.search(r'finish\(answer=["\'](.*)["\']\)', action_str).group(1)
            print(f"最终答案: {final_answer}")
            break

        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        # 支持单引号和双引号
        kwargs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', args_str))

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f'错误：未定义工具 "{tool_name}"'

        observation_str = f"Observation: {observation}"
        print(f'{observation_str}\n' + '=' * 80)
        prompt_history.append(observation_str)
```





## 4 执行

```python
if __name__ == "__main__": main()
```

结果输出如下

```
用户输入: 帮我查询今天广州的天气，根据今天的天气推荐几个合适的旅游景点，输出要详细
========================================
--- 第1轮思考 ---
Generating text with model: deepseek-chat
Generated answer: 
Thought:用户需要查询广州的天气，并根据天气推荐旅游景点。首先，我需要使用get_weather工具获取广州的实时天气信息。

Action:get_weather(city='广州')
LLM输出: 
Thought:用户需要查询广州的天气，并根据天气推荐旅游景点。首先，我需要使用get_weather工具获取广州的实时天气信息。

Action:get_weather(city='广州')
Observation: 错误：查询天气遇到网络问题: HTTPSConnectionPool(host='wttr.in', port=443): Max retries exceeded with url: /%E5%B9%BF%E5%B7%9E?format=j1 (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1032)')))
================================================================================
--- 第2轮思考 ---
Generating text with model: deepseek-chat
Generated answer: 
Thought:获取天气时遇到网络错误，可能是临时问题。我应该重试，最多三次。这是第一次重试。

Action:get_weather(city='广州')
LLM输出: 
Thought:获取天气时遇到网络错误，可能是临时问题。我应该重试，最多三次。这是第一次重试。

Action:get_weather(city='广州')
Observation: 广州当前天气：Clear, 气温：16 摄氏度
================================================================================
--- 第3轮思考 ---
Generating text with model: deepseek-chat
Generated answer: 
Thought:成功获取到广州的天气信息：晴朗，气温16摄氏度。接下来，我需要根据这个天气信息，使用get_attraction工具搜索推荐的旅游景点。

Action:get_attraction(city='广州', weather='Clear')
LLM输出: 
Thought:成功获取到广州的天气信息：晴朗，气温16摄氏度。接下来，我需要根据这个天气信息，使用get_attraction工具搜索推荐的旅游景点。

Action:get_attraction(city='广州', weather='Clear')
Observation: 广州在晴天下值得去的旅游景点有广州塔和珠江新城，这些地方风景优美，适合观光和拍照。
================================================================================
--- 第4轮思考 ---
Generating text with model: deepseek-chat
Generated answer: 
Thought:我已经收集到了足够的信息：广州今天天气晴朗，气温16摄氏度，根据这个天气，推荐的景点是广州塔和珠江新城。现在我可以提供详细的回答，包括天气信息和景点推荐。

Action:finish(answer="根据查询，广州今天的天气为 **晴朗**，气温 **16 摄氏度**，非常适合户外活动。\n\n基于这样的好天气，我为您推荐以下旅游景点：\n\n1. **广州塔**：作为广州的地标建筑，在晴朗天气下登塔可以俯瞰整个城市的美景，视野极佳，非常适合观光和拍照。\n2. **珠江新城**：这里是广州的现代商务中心，拥有花城广场、广州图书馆、广东省博物馆等众多现代化建筑和公共空间。天气晴朗时，在这里散步、欣赏城市天际线和珠江景色会是非常惬意的体验。\n\n这两个景点都位于市区，交通便利，在晴朗的天气下能充分展现其魅力。建议您做好防晒，享受愉快的旅程！")
LLM输出: 
Thought:我已经收集到了足够的信息：广州今天天气晴朗，气温16摄氏度，根据这个天气，推荐的景点是广州塔和珠江新城。现在我可以提供详细的回答，包括天气信息和景点推荐。

Action:finish(answer="根据查询，广州今天的天气为 **晴朗**，气温 **16 摄氏度**，非常适合户外活动。\n\n基于这样的好天气，我为您推荐以下旅游景点：\n\n1. **广州塔**：作为广州的地标建筑，在晴朗天气下登塔可以俯瞰整个城市的美景，视野极佳，非常适合观光和拍照。\n2. **珠江新城**：这里是广州的现代商务中心，拥有花城广场、广州图书馆、广东省博物馆等众多现代化建筑和公共空间。天气晴朗时，在这里散步、欣赏城市天际线和珠江景色会是非常惬意的体验。\n\n这两个景点都位于市区，交通便利，在晴朗的天气下能充分展现其魅力。建议您做好防晒，享受愉快的旅程！")
最终答案: 根据查询，广州今天的天气为 **晴朗**，气温 **16 摄氏度**，非常适合户外活动。\n\n基于这样的好天气，我为您推荐以下旅游景点：\n\n1. **广州塔**：作为广州的地标建筑，在晴朗天气下登塔可以俯瞰整个城市的美景，视野极佳，非常适合观光和拍照。\n2. **珠江新城**：这里是广州的现代商务中心，拥有花城广场、广州图书馆、广东省博物馆等众多现代化建筑和公共空间。天气晴朗时，在这里散步、欣赏城市天际线和珠江景色会是非常惬意的体验。\n\n这两个景点都位于市区，交通便利，在晴朗的天气下能充分展现其魅力。建议您做好防晒，享受愉快的旅程！
```







