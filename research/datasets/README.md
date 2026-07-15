# Datasets

Interview and knowledge tracing datasets used for training and evaluation.

## Dataset Sources

| Dataset | Source | Used For |
|---------|--------|----------|
| ASSISTments 2009 | Public KT benchmark | BKT/DKT baseline training |
| ASSISTments 2015 | Public KT benchmark | DKT evaluation |
| EdNet | Korean AI tutor | Large-scale KT |
| Custom Interview QA | Generated in M1.3 | Interview question bank |

## Data Format (Custom Interview QA)

```json
{
  "question_id": "q001",
  "topic": "DSA",
  "subtopic": "Binary Trees",
  "difficulty": 3,
  "question_text": "...",
  "expected_concepts": ["recursion", "DFS", "time complexity"],
  "sample_answer": "...",
  "hint": "..."
}
```

## Privacy Notice

No real candidate interview data should ever be committed to this repository.
Use only synthetic or publicly licensed datasets.
