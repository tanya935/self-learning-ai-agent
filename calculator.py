def calculator(a, operator, b):

    if operator == "+":
        return a + b

    elif operator == "-":
        return a - b

    elif operator == "*":
        return a * b

    elif operator == "/":
        return a / b

    else:
        return "Unknown operation"