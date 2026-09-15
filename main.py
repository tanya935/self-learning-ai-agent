from ollama import chat

from calculator import calculator
from web_search import search

from memory import (
    load_memory,
    save_fact,
    save_conversation
)

from evaluator import evaluate_response

from learning import (
    save_learning,
    get_good_learning,
    get_learning_patterns
)

import json


MODEL = "llama3.2"


# ==================================================
# 1. AI DECISION MAKER
# ==================================================

def ask_agent(user_input):

    memory = load_memory()

    facts = memory.get("facts", [])

    facts_text = "\n".join(
        f"- {fact}"
        for fact in facts
    )

    if not facts_text:
        facts_text = "No saved facts."


    # ----------------------------------------------
    # LOAD SUCCESSFUL LEARNING
    # ----------------------------------------------

    learning_patterns = get_learning_patterns(
        limit=10
    )

    learning_text = ""

    for pattern in learning_patterns:

        learning_text += f"""
Previous successful experience:

User:
{pattern["user"]}

Successful response:
{pattern["successful_response"]}

Score:
{pattern["score"]}

"""


    if not learning_text:

        learning_text = (
            "No previous successful experiences."
        )


    # ----------------------------------------------
    # DECISION PROMPT
    # ----------------------------------------------

    prompt = f"""
You are the decision-making brain of a
self-learning AI agent.

Your job is to decide which tool/action
should handle the user's request.

Available actions:

calculator
search
memory
answer


==================================================
SAVED USER FACTS
==================================================

{facts_text}


==================================================
SUCCESSFUL LEARNING EXPERIENCES
==================================================

{learning_text}


==================================================
CURRENT USER REQUEST
==================================================

{user_input}


==================================================
LEARNING
==================================================

Previous successful experiences show how the
agent successfully handled similar requests.

Use them as guidance.

If the current request is semantically similar
to a successful previous interaction, prefer
the same useful action.

Do not blindly copy the previous answer.

Understand the current request first.


==================================================
ACTION SELECTION
==================================================

MEMORY
-------

Use memory when the user asks about:

- themselves
- their interests
- what they like
- what they are learning
- their skills
- their preferences
- information previously saved about them


CALCULATOR
----------

Use calculator when the user asks for
a mathematical calculation.

Calculator JSON must contain:

action
a
operator
b


SEARCH
------

Use search when the user needs:

- current information
- latest information
- recent information
- external information
- web information


ANSWER
------

Use answer for general questions that do not
need memory, calculation, or web search.


==================================================
IMPORTANT
==================================================

Return ONLY ONE JSON object.

Do not add explanations.

Do not add markdown.

Do not add extra fields.

Use exactly one of these formats:

{{"action":"memory","query":"What does the user like?"}}

{{"action":"calculator","a":20,"operator":"+","b":30}}

{{"action":"search","query":"latest Python version"}}

{{"action":"answer"}}


==================================================
FINAL RULE
==================================================

If the user asks about their own information
and that information exists in SAVED USER FACTS,
choose MEMORY.

The current request is:

{user_input}
"""


    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json"
    )

    return response["message"]["content"]


# ==================================================
# 2. EXTRACT PERSONAL FACT
# ==================================================

def extract_fact(user_input):

    prompt = f"""
You are the memory system of an AI agent.

Read the user's message.

If the user gives useful personal information,
extract ONE clear fact.

Example:

User:
I am learning Python

Return:

{{"remember":true,"fact":"User is learning Python"}}


Example:

User:
I like machine learning

Return:

{{"remember":true,"fact":"User likes machine learning"}}


If there is no useful personal information:

{{"remember":false,"fact":""}}


Rules:

- Do not create vague facts.
- Do not create facts from questions.
- Do not invent information.
- Use the exact useful information from the user.
- Return ONLY JSON.
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json"
    )

    return parse_json(
        response["message"]["content"]
    ) or {
        "remember": False,
        "fact": ""
    }


# ==================================================
# 3. USE MEMORY
# ==================================================

def use_memory(query):

    memory = load_memory()

    facts = memory.get(
        "facts",
        []
    )

    if not facts:

        return (
            "I don't have any saved "
            "information about that."
        )


    facts_text = "\n".join(
        f"- {fact}"
        for fact in facts
    )


    prompt = f"""
You are the memory retrieval system.

Saved facts:

{facts_text}


User question:

{query}


Find the most relevant saved information.

Rules:

- Use ONLY saved facts.
- Do not guess.
- Do not invent information.
- Answer directly.
- Keep the answer short.
"""


    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


# ==================================================
# 4. GENERATE FINAL ANSWER
# ==================================================

def generate_response(
    user_input,
    tool_result
):

    prompt = f"""
You are the final response generator.

User:

{user_input}


Information:

{tool_result}


Give a natural and concise answer.

Do not mention internal tools,
JSON, evaluation, or agent architecture.
"""


    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


# ==================================================
# 5. PARSE JSON
# ==================================================

def parse_json(text):

    start = text.find("{")

    end = text.rfind("}")


    if start == -1 or end == -1:

        return None


    try:

        return json.loads(
            text[start:end + 1]
        )

    except json.JSONDecodeError:

        return None


# ==================================================
# 6. MAIN LOOP
# ==================================================

print("AI Agent started.")
print("Type 'exit' to stop.")
print()


while True:

    user_input = input("You: ")


    # ----------------------------------------------
    # EXIT
    # ----------------------------------------------

    if user_input.lower().strip() == "exit":

        print("Agent: Goodbye!")

        break


    # ----------------------------------------------
    # EXTRACT PERSONAL INFORMATION
    # ----------------------------------------------

    fact_data = extract_fact(
        user_input
    )


    if fact_data.get("remember"):

        fact = fact_data.get(
            "fact",
            ""
        ).strip()


        if fact:

            save_fact(fact)

            print(
                "Memory updated."
            )


    # ----------------------------------------------
    # AI DECISION
    # ----------------------------------------------

    decision_text = ask_agent(
        user_input
    )


    # ----------------------------------------------
    # PARSE DECISION
    # ----------------------------------------------

    decision = parse_json(
        decision_text
    )


    print(
        "AI decision:",
        decision
    )


    if decision is None:

        print(
            "Agent: I couldn't understand my decision."
        )

        continue


    action = decision.get(
        "action"
    )


    # ==============================================
    # CALCULATOR
    # ==============================================

    if action == "calculator":

        if (
            "a" not in decision
            or "operator" not in decision
            or "b" not in decision
        ):

            print(
                "Agent: Calculator information is incomplete."
            )

            continue


        try:

            result = calculator(
                decision["a"],
                decision["operator"],
                decision["b"]
            )


            final_answer = generate_response(
                user_input,
                f"The calculator returned: {result}"
            )


        except Exception as e:

            final_answer = (
                f"Calculator error: {e}"
            )


    # ==============================================
    # SEARCH
    # ==============================================

    elif action == "search":

        query = decision.get(
            "query"
        )


        if not query:

            print(
                "Agent: Search query is missing."
            )

            continue


        try:

            result = search(
                query
            )


            final_answer = generate_response(
                user_input,
                result
            )


        except Exception as e:

            final_answer = (
                f"Search error: {e}"
            )


    # ==============================================
    # MEMORY
    # ==============================================

    elif action == "memory":

        query = decision.get(
            "query",
            user_input
        )


        final_answer = use_memory(
            query
        )


    # ==============================================
    # NORMAL ANSWER
    # ==============================================

    elif action == "answer":

        final_answer = generate_response(
            user_input,
            "No external tool was required."
        )


    # ==============================================
    # UNKNOWN ACTION
    # ==============================================

    else:

        final_answer = (
            "I don't know how to handle "
            "that request yet."
        )


    # ----------------------------------------------
    # FINAL ANSWER
    # ----------------------------------------------

    print(
        "Agent:",
        final_answer
    )


    # ----------------------------------------------
    # SELF EVALUATION
    # ----------------------------------------------

    try:

        evaluation = evaluate_response(
            user_input,
            final_answer
        )


        print(
            "Self-Evaluation:",
            evaluation
        )


    except Exception as e:

        evaluation = {
            "score": 1,
            "good": False,
            "reason": "Evaluation failed."
        }


        print(
            "Self-Evaluation failed:",
            e
        )


    # ----------------------------------------------
    # SAVE LEARNING
    # ----------------------------------------------

    try:

        save_learning(
            user_input,
            final_answer,
            evaluation
        )


        print(
            "Learning saved."
        )


    except Exception as e:

        print(
            "Learning could not be saved:",
            e
        )


    # ----------------------------------------------
    # SAVE CONVERSATION
    # ----------------------------------------------

    try:

        save_conversation(
            user_input,
            final_answer
        )


    except Exception as e:

        print(
            "Conversation could not be saved:",
            e
        )