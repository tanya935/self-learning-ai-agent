# Self-Learning AI Agent

## Overview

Self-Learning AI Agent is a locally running AI agent built with Python, Ollama, and Llama 3.2.

The agent can understand a user's request, decide which action is required, use available tools, generate a response, evaluate the response, store successful interactions, and learn from user corrections.

The project demonstrates the basic architecture of an AI agent with decision-making, tool usage, memory, evaluation, and learning capabilities.

## Key Features

- AI-based action selection
- Calculator tool for mathematical operations
- Web search for current and external information
- Persistent user memory
- Response self-evaluation
- Learning from successful interactions
- User correction and preference system
- Local Llama 3.2 model through Ollama
- Streamlit-based user interface

## System Architecture

```text
User Input
    |
    v
Llama 3.2
    |
    v
Decision Making
    |
    +------------------+
    |        |         |
    v        v         v
Calculator Search    Memory
    |        |         |
    +--------+---------+
             |
             v
       Final Response
             |
             v
       Self-Evaluation
             |
             v
          Learning
             |
             v
     Future Improvement