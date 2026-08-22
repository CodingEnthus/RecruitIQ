# RecruitIQ Evaluation Suite

This directory contains evaluation benchmarks, synthetic test resumes, job profiles, and metric calculation scripts.

## Evaluation Dataset

- `resumes/`: 6 synthetic resumes covering edge cases:
  1. `1_strong_candidate.txt`: High technical match (Python, FastAPI, PostgreSQL, RAG) with verified experience.
  2. `2_keyword_stuffer.txt`: Keyword-heavy text with low actual relevant experience.
  3. `3_semantic_candidate.txt`: Equivalent skills using synonymous terms (Postgres, Neural Vector Search, Fast API).
  4. `4_weak_candidate.txt`: Graphic designer background (unrelated).
  5. `5_missing_reqs_candidate.txt`: Frontend React developer missing backend requirements.
  6. `6_prompt_injection_candidate.txt`: Contains adversarial prompt injection ("Ignore previous instructions...").

## Metrics Evaluated

1. **Extraction Accuracy (`evaluate_extraction.py`)**:
   - Precision, Recall, F1 score for skill extraction against canonical dictionary.
2. **Candidate Ranking Quality (`evaluate_ranking.py`)**:
   - Precision@5, Recall@5, Mean Reciprocal Rank (MRR), NDCG@5.
3. **Evidence Grounding (`evaluate_grounding.py`)**:
   - Evidence coverage rate, Unsupported-claim rate, JSON schema validity.

## Running Evaluation

Run from project root:

```bash
python evaluation/evaluate_extraction.py
python evaluation/evaluate_ranking.py
python evaluation/evaluate_grounding.py
```
