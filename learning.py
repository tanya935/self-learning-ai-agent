import json
import os


LEARNING_FILE = "learning.json"


def load_learning():

    if not os.path.exists(LEARNING_FILE):
        return []

    try:

        with open(LEARNING_FILE, "r") as file:
            return json.load(file)

    except json.JSONDecodeError:

        return []


def save_learning(user_input, agent_response, evaluation):

    learning = load_learning()

    score = evaluation.get("score", 0)

    learning.append({
        "user": user_input,
        "agent_response": agent_response,
        "evaluation": evaluation,
        "successful": score >= 3
    })

    with open(LEARNING_FILE, "w") as file:

        json.dump(
            learning,
            file,
            indent=4
        )


def get_good_learning(limit=10):

    learning = load_learning()

    good_examples = []

    for item in learning:

        if item.get("successful") is True:

            good_examples.append(item)

    return good_examples[-limit:]


def get_learning_patterns(limit=10):

    learning = get_good_learning(limit)

    patterns = []

    for item in learning:

        patterns.append({
            "user": item.get("user", ""),
            "successful_response": item.get(
                "agent_response",
                ""
            ),
            "score": item.get(
                "evaluation",
                {}
            ).get(
                "score",
                0
            )
        })

    return patterns