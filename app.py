import streamlit as st
import json

from ollama import chat

from calculator import calculator
from web_search import search

from memory import (
    load_memory,
    save_conversation,
    save_fact,
    get_recent_memory,
    get_facts,
    save_knowledge,
    get_knowledge,
    search_knowledge
)

from evaluator import evaluate_response

from learning import (
    save_learning,
    get_good_learning
)

from corrections import (
    save_correction,
    get_corrections
)


# =========================================================
# CONFIGURATION
# =========================================================

MODEL = "llama3.2"


# =========================================================
# AUTOMATIC KNOWLEDGE EXTRACTION
# =========================================================

def extract_knowledge(user_input):

    prompt = f"""
You are a knowledge extraction system.

Analyze the user's message and decide whether it contains
a useful factual statement that should be remembered for
future questions.

Save only useful factual information.

Do NOT save:

- questions
- greetings
- casual conversation
- temporary feelings
- opinions
- commands
- corrections
- random conversation

Examples:

User:
Python was created by Guido van Rossum.

Output:
{{
    "remember": true,
    "statement": "Python was created by Guido van Rossum.",
    "topic": "Python"
}}

User:
I am tired today.

Output:
{{
    "remember": false,
    "statement": "",
    "topic": ""
}}

User:
What is Python?

Output:
{{
    "remember": false,
    "statement": "",
    "topic": ""
}}

User:
I think Python is the best language.

Output:
{{
    "remember": false,
    "statement": "",
    "topic": ""
}}

User message:
{user_input}

Return ONLY valid JSON.
"""

    try:

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response["message"]["content"].strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

        result = json.loads(content)

        return result

    except Exception:

        return {
            "remember": False,
            "statement": "",
            "topic": ""
        }


# =========================================================
# CORRECTION DETECTION
# =========================================================

def detect_correction(user_input):

    prompt = f"""
You are a correction detector for an AI agent.

Determine whether the user's message is correcting
the agent's previous behavior or answer.

Normal questions and normal statements are NOT corrections.

Examples that are NOT corrections:

"My name is Aprajita."

"The PM of India is Narendra Modi."

"I am learning Python."

"What is Python?"

"Explain database."

Examples of corrections:

"No, explain Python in very simple language."

"Don't give such a long answer."

"Next time give an example."

"You misunderstood my question."

"Explain this in Hindi."

Return ONLY valid JSON.

Format:

{{
    "is_correction": true,
    "topic": "...",
    "instruction": "..."
}}

OR

{{
    "is_correction": false,
    "topic": "",
    "instruction": ""
}}

User message:
{user_input}
"""

    try:

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response["message"]["content"].strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

        return json.loads(content)

    except Exception:

        return {
            "is_correction": False,
            "topic": "",
            "instruction": ""
        }


# =========================================================
# AI DECISION MAKER
# =========================================================

def ask_agent(user_input):

    facts = get_facts()
    knowledge = get_knowledge()

    recent_memory = get_recent_memory()

    knowledge_text = ""

    for item in knowledge[-10:]:

        knowledge_text += (
            f"- {item.get('statement', '')} "
            f"(topic: {item.get('topic', '')})\n"
        )

    facts_text = "\n".join(f"- {fact}" for fact in facts)

    memory_text = ""

    for item in recent_memory[-5:]:

        memory_text += (
            f"User: {item.get('user', '')}\n"
            f"Agent: {item.get('agent', '')}\n"
        )

    prompt = f"""
You are the decision-making brain of an AI agent.

Your job is to decide which action should be used
to answer the user's question.

Available actions:

1. calculator
2. search
3. memory
4. knowledge
5. answer

Rules:

calculator:
Use for mathematical calculations.

search:
Use when the user asks for:
- latest information
- current information
- recent information
- today's information
- live information
- external information
- changing information
- information you are not confident about

For current or latest information, DO NOT rely only
on internal knowledge or old memory.

memory:
Use when the user asks about personal information
that has been saved about the user.

knowledge:
Use when the answer can be found in the saved
general knowledge provided by the user.

answer:
Use for normal stable general knowledge when
web search is not necessary.

Important:

If a question is about a current or changing fact,
prefer SEARCH even if saved knowledge contains an
older answer.

Saved personal facts:
{facts_text}

Saved general knowledge:
{knowledge_text}

Recent conversation:
{memory_text}

User question:
{user_input}

Return ONLY valid JSON.

Format:

{{
    "action": "calculator",
    "reason": "..."
}}

or

{{
    "action": "search",
    "reason": "..."
}}

or

{{
    "action": "memory",
    "reason": "..."
}}

or

{{
    "action": "knowledge",
    "reason": "..."
}}

or

{{
    "action": "answer",
    "reason": "..."
}}
"""

    try:

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response["message"]["content"].strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

        decision = json.loads(content)

        return decision

    except Exception:

        return {
            "action": "answer",
            "reason": "Defaulting to general answer."
        }


# =========================================================
# MEMORY RESPONSE
# =========================================================

def use_memory(user_input):

    facts = get_facts()

    knowledge = get_knowledge()

    recent_memory = get_recent_memory()

    memory_text = f"""
Saved personal facts:

{facts}

Saved general knowledge:

{knowledge}

Recent conversations:

{recent_memory}

User question:

{user_input}
"""

    prompt = f"""
Answer the user's question using the available memory.

Do not invent information.

If the required information is not present,
say that it is not available in memory.

Memory:
{memory_text}
"""

    try:

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

    except Exception as e:

        return f"Memory response failed: {e}"


# =========================================================
# KNOWLEDGE RESPONSE
# =========================================================

def use_knowledge(user_input):

    results = search_knowledge(user_input)

    if not results:

        return "I could not find relevant information in my saved knowledge."

    knowledge_text = ""

    for item in results:

        knowledge_text += (
            f"Statement: {item.get('statement', '')}\n"
            f"Topic: {item.get('topic', '')}\n\n"
        )

    prompt = f"""
Answer the user's question using the saved knowledge below.

Use only information that is relevant to the question.

Do not invent information.

Saved knowledge:

{knowledge_text}

User question:

{user_input}

Give a clear and simple answer.
"""

    try:

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

    except Exception as e:

        return f"Knowledge response failed: {e}"


# =========================================================
# FINAL RESPONSE GENERATOR
# =========================================================

def generate_response(
    user_input,
    tool_result="",
    action="answer"
):

    corrections = get_corrections()

    correction_text = ""

    for correction in corrections:

        correction_text += (
            f"Topic: {correction.get('topic', '')}\n"
            f"Instruction: {correction.get('instruction', '')}\n\n"
        )

    prompt = f"""
You are the final response generator of an AI agent.

User question:

{user_input}

Action used:

{action}

Information from tool:

{tool_result}

Saved corrections:

{correction_text}

Instructions:

1. Give a clear and useful answer.
2. Do not invent information.
3. If web search information is provided, use that information.
4. Do not claim something is current unless current information
   was actually obtained from web search.
5. Apply a saved correction ONLY if it clearly matches
   the current question.
6. Do not apply unrelated corrections.

Example:

Saved correction:
"Explain Python in very simple language."

Current question:
"My name is Aprajita."

Do NOT apply the Python correction.

Current question:
"What is Python?"

Apply the Python correction.

Answer the user naturally.
"""

    try:

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

    except Exception as e:

        return f"Response generation failed: {e}"


# =========================================================
# STREAMLIT UI
# =========================================================

st.set_page_config(
    page_title="Self Learning AI Agent",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 Self-Learning AI Agent")

st.write(
    "AI agent powered by Llama 3.2, Ollama, memory, "
    "web search and learning."
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🧠 Agent Memory")

    facts = get_facts()

    if facts:

        st.subheader("Personal Facts")

        for fact in facts:

            st.write("•", fact)

    knowledge = get_knowledge()

    if knowledge:

        st.subheader("General Knowledge")

        for item in knowledge[-10:]:

            st.write(
                "•",
                item.get("statement", "")
            )

    corrections = get_corrections()

    if corrections:

        st.subheader("Learned Corrections")

        for correction in corrections:

            st.write(
                "•",
                correction.get("instruction", "")
            )

    good_learning = get_good_learning()

    st.subheader("Learning Records")

    st.write(
        f"Successful interactions: {len(good_learning)}"
    )


# =========================================================
# CHAT HISTORY
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


# =========================================================
# USER INPUT
# =========================================================

user_input = st.chat_input(
    "Ask me anything..."
)


if user_input:

    # -----------------------------------------------------
    # Show user message
    # -----------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):

        st.write(user_input)


    # -----------------------------------------------------
    # STEP 1: Check correction
    # -----------------------------------------------------

    correction = detect_correction(user_input)


    if correction.get("is_correction") is True:

        topic = correction.get(
            "topic",
            ""
        ).strip()

        instruction = correction.get(
            "instruction",
            ""
        ).strip()

        if topic and instruction:

            save_correction(
                topic,
                instruction
            )

            agent_response = (
                "Got it. I will remember this correction "
                "and apply it when it is relevant."
            )

        else:

            agent_response = (
                "I understood your correction, "
                "but I could not save it properly."
            )


    else:

        # -------------------------------------------------
        # STEP 2: Extract general knowledge
        # -------------------------------------------------

        knowledge_result = extract_knowledge(
            user_input
        )

        if knowledge_result.get("remember") is True:

            statement = knowledge_result.get(
                "statement",
                ""
            ).strip()

            topic = knowledge_result.get(
                "topic",
                ""
            ).strip()

            if statement:

                save_knowledge(
                    statement,
                    topic
                )


        # -------------------------------------------------
        # STEP 3: Ask AI what to do
        # -------------------------------------------------

        decision = ask_agent(
            user_input
        )

        action = decision.get(
            "action",
            "answer"
        )


        # -------------------------------------------------
        # STEP 4: Execute selected action
        # -------------------------------------------------

        if action == "calculator":

            tool_result = (
                "The calculator action was selected. "
                "Use the calculator tool when the "
                "question contains a mathematical expression."
            )

            agent_response = generate_response(
                user_input,
                tool_result,
                action
            )


        elif action == "search":

            tool_result = search(
                user_input
            )

            agent_response = generate_response(
                user_input,
                tool_result,
                action
            )


        elif action == "memory":

            tool_result = use_memory(
                user_input
            )

            agent_response = generate_response(
                user_input,
                tool_result,
                action
            )


        elif action == "knowledge":

            tool_result = use_knowledge(
                user_input
            )

            agent_response = generate_response(
                user_input,
                tool_result,
                action
            )


        else:

            agent_response = generate_response(
                user_input,
                "",
                "answer"
            )


        # -------------------------------------------------
        # STEP 5: Evaluate response
        # -------------------------------------------------

        evaluation = evaluate_response(
            user_input,
            agent_response
        )


        # -------------------------------------------------
        # STEP 6: Save learning
        # -------------------------------------------------

        save_learning(
            user_input,
            agent_response,
            evaluation
        )


        # -------------------------------------------------
        # STEP 7: Save conversation
        # -------------------------------------------------

        save_conversation(
            user_input,
            agent_response
        )


    # -----------------------------------------------------
    # Show response
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        st.write(agent_response)


    st.session_state.messages.append({
        "role": "assistant",
        "content": agent_response
    })