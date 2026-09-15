import re


def evaluate_response(user_input, agent_response):

    question = user_input.lower().strip()
    answer = agent_response.lower().strip()


    # ================================================
    # PERSONAL MEMORY QUESTIONS
    # ================================================

    personal_questions = [
        "what do i like",
        "what are my interests",
        "what am i learning",
        "what programming language do i like",
        "what skills am i learning"
    ]


    for q in personal_questions:

        if q in question:

            # If the agent actually returned useful information
            # instead of saying it doesn't know
            bad_answers = [
                "i don't know",
                "i don't have that information",
                "i couldn't",
                "i am not sure"
            ]

            for bad in bad_answers:

                if bad in answer:

                    return {
                        "score": 1,
                        "good": False,
                        "reason": "The agent did not provide the requested personal information."
                    }


            # A non-empty direct response is considered successful
            if len(answer) > 0:

                return {
                    "score": 3,
                    "good": True,
                    "reason": "The agent directly answered the personal question using available information."
                }


    # ================================================
    # EMPTY RESPONSE
    # ================================================

    if not answer:

        return {
            "score": 1,
            "good": False,
            "reason": "The agent returned an empty response."
        }


    # ================================================
    # GENERAL RESPONSE
    # ================================================

    # For general questions we currently use
    # a simple quality check.

    if len(answer) < 5:

        return {
            "score": 2,
            "good": False,
            "reason": "The response is too short to evaluate confidently."
        }


    return {
        "score": 3,
        "good": True,
        "reason": "The agent provided a non-empty response."
    }