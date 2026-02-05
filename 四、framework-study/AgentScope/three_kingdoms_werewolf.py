import agentscope
from agentscope.agents import DictDialogAgent
from agentscope.pipelines import SequentialPipeline
from agentscope.message import Msg
from agentscope.msghub import msghub
import json

import os

# Define the model configuration
# NOTE: You need to fill in your API key here or use a local model
api_key = os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
model_config = {
    "config_name": "my_openai_config",
    "model_type": "openai_chat",
    "config": {
        "model": "gpt-3.5-turbo",
        "api_key": api_key,
    }
}

# Define the prompts for Three Kingdoms characters
# We map standard Werewolf roles to Three Kingdoms characters
# Werewolf: Cao Cao (曹操), Sima Yi (司马懿)
# Villager: Liu Bei (刘备), Sun Quan (孙权)
# Seer: Zhuge Liang (诸葛亮)
# Witch: Diao Chan (貂蝉)

PROMPTS = {
    "Cao Cao": {
        "role": "werewolf",
        "desc": "你是曹操，乱世之奸雄。在狼人杀游戏中，你的身份是【狼人】。你需要隐藏身份，假装好人，并在夜晚与队友商量杀谁。请表现出你的霸气和多疑。",
    },
    "Sima Yi": {
        "role": "werewolf",
        "desc": "你是司马懿，深谋远虑。在狼人杀游戏中，你的身份是【狼人】。你需要配合曹操，隐藏身份。请表现出你的隐忍和阴险。",
    },
    "Liu Bei": {
        "role": "villager",
        "desc": "你是刘备，仁义之君。在狼人杀游戏中，你的身份是【平民】。你不知道谁是狼人，需要通过发言找出狼人。请表现出你的仁德。",
    },
    "Sun Quan": {
        "role": "villager",
        "desc": "你是孙权，江东霸主。在狼人杀游戏中，你的身份是【平民】。你要保护江东子弟，找出狼人。请表现出你的决断。",
    },
    "Zhuge Liang": {
        "role": "seer",
        "desc": "你是诸葛亮，神机妙算。在狼人杀游戏中，你的身份是【预言家】。每晚你可以查验一个人的身份。请表现出你的智慧。",
    },
    "Diao Chan": {
        "role": "witch",
        "desc": "你是貂蝉，闭月羞花。在狼人杀游戏中，你的身份是【女巫】。你有一瓶解药和一瓶毒药。请表现出你的柔情与机智。",
    }
}

def main():
    if api_key == "YOUR_API_KEY_HERE":
        print("Warning: Please set your OPENAI_API_KEY environment variable or edit the script to add your key.")
        # We continue, but it might fail if the model requires a real key.
    
    # Initialize AgentScope
    try:
        agentscope.init(model_configs=[model_config])
    except Exception as e:
        print(f"Initialization failed (likely due to missing API key or config): {e}")
        return

    # Create Agents
    agents = []
    for name, info in PROMPTS.items():
        sys_prompt = f"""
        {info['desc']}
        
        游戏规则：
        1. 这是一个6人局：2狼人，2平民，1预言家，1女巫。
        2. 请用JSON格式回复，包含 "thought" (思考) 和 "speak" (发言) 两个字段。
        3. 如果是投票环节，请额外包含 "vote" 字段（目标玩家名字）。
        4. 如果是夜晚行动环节，请包含 "action" 字段（如杀谁、查验谁、救/毒谁）。
        """
        
        agent = DictDialogAgent(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name="my_openai_config",
            use_memory=True
        )
        agents.append(agent)

    # Separate agents by role for easier access
    wolves = [a for a in agents if PROMPTS[a.name]["role"] == "werewolf"]
    villagers = [a for a in agents if PROMPTS[a.name] == "villager"] # Bug here: PROMPTS[a.name] is a dict
    seer = [a for a in agents if PROMPTS[a.name]["role"] == "seer"][0]
    witch = [a for a in agents if PROMPTS[a.name]["role"] == "witch"][0]
    
    # Corrected access
    villagers = [a for a in agents if PROMPTS[a.name]["role"] == "villager"]

    # Game Loop (Simplified: 1 Night + 1 Day)
    
    # --- Night Phase ---
    print("\n=== 天黑请闭眼 ===\n")
    
    # 1. Werewolves discuss
    with msghub(wolves, announcement=Msg(name="System", content="狼人请睁眼。请商量今晚杀谁？")):
        # Simple sequential discussion
        x = Msg(name="System", content="请开始讨论。")
        for wolf in wolves:
            x = wolf(x)
            print(f"[{wolf.name}] {x.content.get('speak')}")
            
    # 2. Seer checks
    print("\n=== 预言家请睁眼 ===\n")
    # In a real game, Seer would choose someone. Here we simplify.
    x = Msg(name="System", content="请选择你要查验的玩家。")
    res = seer(x)
    print(f"[{seer.name}] {res.content.get('thought')}")
    
    # 3. Witch acts
    print("\n=== 女巫请睁眼 ===\n")
    x = Msg(name="System", content="今晚有人被杀（模拟），你要使用解药或毒药吗？")
    res = witch(x)
    print(f"[{witch.name}] {res.content.get('thought')}")

    # --- Day Phase ---
    print("\n=== 天亮了 ===\n")
    
    # Everyone discusses
    with msghub(agents, announcement=Msg(name="System", content="昨晚是平安夜（模拟）。现在开始自由讨论，找出狼人。")):
        x = Msg(name="System", content="请大家发言。")
        # Let each agent speak once
        for agent in agents:
            x = agent(x)
            print(f"[{agent.name}] {x.content.get('speak')}")

if __name__ == "__main__":
    main()
