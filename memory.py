import json
import os


MEMORY_FILE = "memory.json"


def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return {
            "conversations": [],
            "facts": [],
            "knowledge": []
        }

    try:

        with open(MEMORY_FILE, "r") as file:
            memory = json.load(file)

        # Old memory.json compatibility
        if isinstance(memory, list):
            return {
                "conversations": memory,
                "facts": [],
                "knowledge": []
            }

        # If knowledge section does not exist
        if "knowledge" not in memory:
            memory["knowledge"] = []

        if "facts" not in memory:
            memory["facts"] = []

        if "conversations" not in memory:
            memory["conversations"] = []

        return memory

    except (json.JSONDecodeError, OSError):

        return {
            "conversations": [],
            "facts": [],
            "knowledge": []
        }


# -------------------------
# Conversation Memory
# -------------------------

def save_conversation(user_input, agent_response):

    memory = load_memory()

    memory["conversations"].append({
        "user": user_input,
        "agent": agent_response
    })

    with open(MEMORY_FILE, "w") as file:

        json.dump(
            memory,
            file,
            indent=4
        )


def get_recent_memory(limit=10):

    memory = load_memory()

    return memory["conversations"][-limit:]


# -------------------------
# Personal Facts
# -------------------------

def save_fact(fact):

    memory = load_memory()

    if fact not in memory["facts"]:

        memory["facts"].append(fact)

    with open(MEMORY_FILE, "w") as file:

        json.dump(
            memory,
            file,
            indent=4
        )


def get_facts():

    memory = load_memory()

    return memory["facts"]


# -------------------------
# General Knowledge Memory
# -------------------------

def save_knowledge(statement, topic=""):

    memory = load_memory()

    # Prevent duplicate knowledge
    for item in memory["knowledge"]:

        if item.get("statement", "").lower().strip() == statement.lower().strip():

            return

    memory["knowledge"].append({
        "statement": statement,
        "topic": topic,
        "source": "user"
    })

    with open(MEMORY_FILE, "w") as file:

        json.dump(
            memory,
            file,
            indent=4
        )


def get_knowledge():

    memory = load_memory()

    return memory["knowledge"]


def search_knowledge(query):

    memory = load_memory()

    query_words = query.lower().split()

    matches = []

    for item in memory["knowledge"]:

        statement = item.get("statement", "").lower()
        topic = item.get("topic", "").lower()

        text = statement + " " + topic

        score = 0

        for word in query_words:

            if len(word) > 2 and word in text:
                score += 1

        if score > 0:

            matches.append({
                "statement": item.get("statement", ""),
                "topic": item.get("topic", ""),
                "score": score
            })

    matches.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return matches[:5]