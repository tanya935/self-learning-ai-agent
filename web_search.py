from ddgs import DDGS


def search(query):

    print("Searching the web for:", query)

    try:

        results = DDGS().text(
            query,
            max_results=5
        )

        if not results:
            return "No search results found."

        output = ""

        for result in results:

            output += f"""
Title: {result.get('title', '')}
URL: {result.get('href', '')}
Description: {result.get('body', '')}

"""

        return output

    except Exception as e:

        return f"Web search failed: {e}"