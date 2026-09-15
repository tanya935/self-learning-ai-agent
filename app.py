import streamlit as st
import json

from ollama import chat

from calculator import calculator
from web_search import search
from memory import load_memory, save_conversation
from evaluator import evaluate_response
from learning import save_learning, get_good_learning
from corrections import save_correction, get_corrections


MODEL = "llama3.2"


# ============================================
# PAGE SETTINGS
# ============================================

st.set_page_config(
    page_title="Self-Learning AI Agent",
    page_icon="🤖",
    layout="centered"
)


# ============================================
# CHAT HISTORY
# ============================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================
# SIDEBAR
# ============================================

with st.sidebar:

    st.title("🤖 AI Agent")

    st.write("### Agent Status")
    st.success("🟢 Online")

    st.write("### Available Tools")

    st.write("🧮 Calculator")
    st.write("🌐 Web Search")
    st.write("🧠 Memory")
    st.write("💬 General Answer")
    st.write("📚 Learning")
    st.write("✏️ Corrections")

    st.divider()

    if st.button("🧹 Clear Chat"):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    # ========================================
    # SAVED MEMORY
    # ========================================

    st.write("### Saved Memory")

    memory = load_memory()

    facts = memory.get("facts", [])

    if facts:

        for fact in facts:

            st.write("•", fact)

    else:

        st.write("No saved facts yet.")

    st.divider()

    # ========================================
    # SAVED CORRECTIONS
    # ========================================

    st.write("### Saved Corrections")

    corrections = get_corrections()

    if corrections:

        for correction in corrections:

            st.write(
                "•",
                correction.get("instruction", "")
            )

    else:

        st.write("No corrections yet.")


# ============================================
# MAIN PAGE
# ============================================

st.title("🤖 Self-Learning AI Agent")

st.write(
    "Ask me a question and the AI will decide "
    "how to handle it."
)


# ============================================
# SHOW PREVIOUS CHAT
# ============================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


# ============================================
# JSON PARSER
# ============================================

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


# ============================================
# CORRECTION DETECTOR
# ============================================

def detect_correction(user_input):

    prompt = f"""
You are the correction detector of a
self-learning AI agent.

User message:

{user_input}

Determine whether the user is correcting,
changing, or giving a preference about
how the AI should answer.

Examples:

"No, give me the definition instead."

"That answer is wrong. Explain it with
an example."

"From now on, keep the answer short."

"I want the definition, not my personal
information."

These are corrections.

A normal question such as:

"What is Python?"

is NOT a correction.

If this is a correction, return:

{{
    "is_correction": true,
    "topic": "the topic being corrected",
    "instruction": "what the AI should do differently"
}}

If this is NOT a correction, return:

{{
    "is_correction": false,
    "topic": "",
    "instruction": ""
}}

Return ONLY JSON.
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
    )


# ============================================
# AI DECISION MAKER
# ============================================

def ask_agent(user_input):

    memory = load_memory()

    facts = memory.get("facts", [])

    facts_text = "\n".join(
        f"- {fact}"
        for fact in facts
    )

    if not facts_text:

        facts_text = "No saved facts."


    # ----------------------------------------
    # PREVIOUS CORRECTIONS
    # ----------------------------------------

    corrections = get_corrections(
        limit=10
    )

    corrections_text = ""

    for correction in corrections:

        corrections_text += f"""
Topic:
{correction.get("topic", "")}

Instruction:
{correction.get("instruction", "")}

"""


    if not corrections_text:

        corrections_text = "No saved corrections."


    # ----------------------------------------
    # PREVIOUS SUCCESSFUL LEARNING
    # ----------------------------------------

    good_examples = get_good_learning(
        limit=5
    )

    learning_text = ""

    for example in good_examples:

        learning_text += f"""
Previous successful interaction:

User:
{example.get("user", "")}

Successful response:
{example.get("agent_response", "")}

"""


    if not learning_text:

        learning_text = (
            "No previous successful examples."
        )


    prompt = f"""
You are the decision-making brain of a
self-learning AI agent.

Available actions:

calculator
search
memory
answer

Saved user facts:

{facts_text}

Saved corrections:

{corrections_text}

Previous successful examples:

{learning_text}

Current user request:

{user_input}


IMPORTANT RULES:

1. Use calculator for mathematical
   calculations.

2. Use search for current, latest,
   recent, or external information.

3. Use memory ONLY when the user asks
   about their personal information.

4. Use answer for normal general
   knowledge questions.

5. Saved personal facts must NOT override
   a general knowledge question.

6. Saved corrections are important.

7. If a saved correction clearly applies
   to the current request, select the
   appropriate action normally and allow
   the final response generator to follow
   that correction.

8. Previous successful examples can help
   improve the answer.

Return ONLY JSON.

Examples:

{{"action":"memory","query":"What does the user like?"}}

{{"action":"calculator","a":20,"operator":"+","b":30}}

{{"action":"search","query":"latest Python version"}}

{{"action":"answer"}}
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


# ============================================
# MEMORY
# ============================================

def use_memory(query):

    memory = load_memory()

    facts = memory.get("facts", [])

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

Use ONLY the saved facts.

Do not guess.

Do not invent information.

Answer directly and briefly.
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


# ============================================
# FINAL RESPONSE
# ============================================

def generate_response(
    user_input,
    information
):

    corrections = get_corrections(
        limit=10
    )

    corrections_text = ""

    for correction in corrections:

        topic = correction.get(
            "topic",
            ""
        )

        instruction = correction.get(
            "instruction",
            ""
        )

        corrections_text += f"""
Topic:
{topic}

IMPORTANT USER INSTRUCTION:
{instruction}

"""


    if not corrections_text:

        corrections_text = "No saved corrections."


    prompt = f"""
You are the final response generator of
a self-learning AI agent.

User question:

{user_input}


Information available:

{information}


USER'S SAVED RESPONSE INSTRUCTIONS:

{corrections_text}


Your job is to answer the user's question.

IMPORTANT RULES:

1. First check whether any saved instruction
   applies to the current question.

2. If an instruction applies, you MUST
   follow EVERY part of that instruction.

3. Do NOT partially follow the instruction.

4. Do NOT ignore any important part of it.

5. If the instruction asks for simple
   language, use simple language.

6. If the instruction asks for an example,
   you MUST include an actual example.

7. If the instruction asks for both simple
   language AND an example, you MUST do BOTH.

8. If the instruction asks for a short answer,
   keep the answer short.

9. If the instruction asks for details,
   provide enough explanation.

10. If multiple instructions apply, follow
    the most recent relevant instruction.

11. If no instruction applies, answer normally.

12. Never mention the saved instruction.

13. Never mention memory.

14. Never mention internal tools.

15. Never mention evaluation.

16. Never mention JSON.

17. Never mention the agent architecture.

18. Answer naturally and directly.


IMPORTANT EXAMPLE:

User question:

What is Python?

Saved instruction:

Explain Python in very simple language
with an example.

The answer MUST look similar in structure
to this:

Python is a programming language that is
easy to learn and is used to give
instructions to a computer.

For example:

print("Hello")

This tells Python to display Hello on
the screen.

The exact wording can be different,
but BOTH the simple explanation and
the example MUST be present.


Now answer the actual user question.

Return ONLY the final answer.
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


# ============================================
# USER INPUT
# ============================================

user_input = st.chat_input(
    "Ask something..."
)


if user_input:

    # ----------------------------------------
    # SAVE USER MESSAGE
    # ----------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    with st.chat_message("user"):

        st.write(user_input)


    # ========================================
    # CHECK FOR CORRECTION
    # ========================================

    correction = detect_correction(
        user_input
    )


    if (
        correction
        and correction.get("is_correction") is True
    ):

        topic = correction.get(
            "topic",
            ""
        )

        instruction = correction.get(
            "instruction",
            ""
        )


        if topic and instruction:

            save_correction(
                topic,
                instruction
            )


            final_answer = (
                "Got it. I have updated my "
                "response preference."
            )

        else:

            final_answer = (
                "I understood that you want "
                "to correct my previous answer."
            )


    # ========================================
    # NORMAL QUESTION
    # ========================================

    else:

        # ------------------------------------
        # AI DECISION
        # ------------------------------------

        decision_text = ask_agent(
            user_input
        )

        decision = parse_json(
            decision_text
        )


        # ------------------------------------
        # EXECUTE ACTION
        # ------------------------------------

        if decision is None:

            final_answer = (
                "I couldn't understand "
                "my decision."
            )

        else:

            action = decision.get(
                "action"
            )


            # ================================
            # CALCULATOR
            # ================================

            if action == "calculator":

                result = calculator(
                    decision["a"],
                    decision["operator"],
                    decision["b"]
                )

                final_answer = generate_response(
                    user_input,
                    f"The calculator returned: {result}"
                )


            # ================================
            # WEB SEARCH
            # ================================

            elif action == "search":

                query = decision.get(
                    "query",
                    user_input
                )

                result = search(query)

                final_answer = generate_response(
                    user_input,
                    result
                )


            # ================================
            # MEMORY
            # ================================

            elif action == "memory":

                query = decision.get(
                    "query",
                    user_input
                )

                final_answer = use_memory(
                    query
                )


            # ================================
            # GENERAL ANSWER
            # ================================

            else:

                final_answer = generate_response(
                    user_input,
                    "No external tool was required."
                )


    # ========================================
    # SELF EVALUATION
    # ========================================

    evaluation = evaluate_response(
        user_input,
        final_answer
    )


    # ========================================
    # SAVE LEARNING
    # ========================================

    save_learning(
        user_input,
        final_answer,
        evaluation
    )


    # ========================================
    # SAVE CONVERSATION
    # ========================================

    save_conversation(
        user_input,
        final_answer
    )


    # ========================================
    # SAVE ASSISTANT MESSAGE
    # ========================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": final_answer
        }
    )


    # ========================================
    # SHOW ANSWER
    # ========================================

    with st.chat_message("assistant"):

        st.write(final_answer)


        if evaluation.get("good"):

            st.caption(
                "🧠 Learned from this interaction."
            )

        else:

            st.caption(
                "🔄 Interaction saved for improvement."
            )