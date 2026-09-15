import json
import os


CORRECTIONS_FILE = "corrections.json"


def load_corrections():

    if not os.path.exists(CORRECTIONS_FILE):
        return []

    try:

        with open(CORRECTIONS_FILE, "r") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return []


def save_correction(topic, instruction):

    corrections = load_corrections()

    # Check if the same topic already exists
    updated = False

    for correction in corrections:

        if correction.get("topic", "").lower().strip() == topic.lower().strip():

            correction["instruction"] = instruction

            updated = True

            break


    # If topic is new, create a new correction
    if not updated:

        corrections.append({
            "topic": topic,
            "instruction": instruction
        })


    with open(CORRECTIONS_FILE, "w") as file:

        json.dump(
            corrections,
            file,
            indent=4
        )


def get_corrections(limit=10):

    corrections = load_corrections()

    return corrections[-limit:]