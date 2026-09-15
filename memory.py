import json
import os


MEMORY_FILE = "memory.json"


def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return {
            "conversations": [],
            "facts": []
        }

    try:

        with open(MEMORY_FILE, "r") as file:
            memory = json.load(file)

        # Agar purana format list hai
        if isinstance(memory, list):

            return {
                "conversations": memory,
                "facts": []
            }

        return memory

    except json.JSONDecodeError:

        return {
            "conversations": [],
            "facts": []
        }


def save_conversation(user_input, agent_response):

    memory = load_memory()

    memory["conversations"].append({
        "user": user_input,
        "agent": agent_response
    })

    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=4)


def save_fact(fact):

    memory = load_memory()

    if fact not in memory["facts"]:

        memory["facts"].append(fact)

    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=4)


def get_recent_memory(limit=10):

    memory = load_memory()

    return memory["conversations"][-limit:]


def get_facts():

    memory = load_memory()

    return memory["facts"]