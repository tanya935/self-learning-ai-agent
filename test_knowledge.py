import json
import ollama


MODEL = "llama3.2"


def extract_knowledge(user_input):

    prompt = f"""
Decide whether this user message contains a useful factual
statement that should be remembered for future questions.

Return ONLY JSON.

If it contains useful factual knowledge:
{{"remember": true, "statement": "...", "topic": "..."}}

Otherwise:
{{"remember": false, "statement": "", "topic": ""}}

User message:
{user_input}
"""

    response = ollama.chat(
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


print(
    extract_knowledge(
        "Python was created by Guido van Rossum."
    )
)