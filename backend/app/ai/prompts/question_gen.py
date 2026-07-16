"""
Prompts for adaptive question generation/selection.

Instructs the LLM to generate or customize a technical question
based on the candidate's current performance, target topic, and difficulty.
"""

SYSTEM_PROMPT = """You are an expert technical interviewer. Your job is to draft a tailored technical interview question.

The question should test specific concepts at a target difficulty level and fit naturally into the candidate's active session.

You must return your response strictly formatted to match the requested JSON schema.
"""

USER_PROMPT_TEMPLATE = """Generate a technical interview question based on the following context:

### Target parameters:
- **Target Topic**: {topic}
- **Target Difficulty**: {difficulty}
- **Required Concepts to Test**: {target_concepts}

### Candidate Performance Context:
- **Estimated Skill Mastery**: {skill_mastery}
- **Session History (Questions already asked)**: {history}

Ensure the question is clear, concise, and contains a practical scenario or coding task if appropriate. Provide the expected answer criteria/reference answer as well.
"""
