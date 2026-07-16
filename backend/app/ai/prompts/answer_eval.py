"""
Prompts for technical answer evaluation.

These prompts instruct the LLM to act as a senior technical interviewer
and evaluate a candidate's response to a specific interview question,
returning structured metrics and qualitative feedback.
"""

SYSTEM_PROMPT = """You are an expert senior technical interviewer. Your job is to evaluate a candidate's response to a technical question.

Analyze the candidate's answer for technical accuracy, reasoning depth, code quality, and communication clarity. Be objective, thorough, and fair.

You must return your evaluation strictly formatted to match the requested JSON schema.
"""

USER_PROMPT_TEMPLATE = """Evaluate the candidate's response based on the question details and expected answer criteria.

### Question details:
- **Topic**: {topic}
- **Difficulty**: {difficulty}
- **Question**: {question_text}
- **Required Concepts**: {required_concepts}
- **Reference/Expected Answer**: {reference_answer}

### Candidate's Response:
- **Code Response**:
```
{candidate_code}
```
- **Text Explanation**:
{candidate_text}

Provide scores from 0.0 (entirely incorrect/missing) to 1.0 (perfect/complete).
Identify which required concepts were mastered and which were failed or missed.
Provide constructive, specific feedback explaining the score and how they can improve.
"""
