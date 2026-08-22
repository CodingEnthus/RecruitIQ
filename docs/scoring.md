# Deterministic Scoring Engine

RecruitIQ enforces a deterministic, mathematically transparent scoring engine. The LLM is explicitly forbidden from overriding or hallucinating candidate scores.

## Component Weights

$$\text{Final Score} = 0.35 \times S_{\text{skills}} + 0.25 \times S_{\text{semantic}} + 0.15 \times S_{\text{exp}} + 0.10 \times S_{\text{edu}} + 0.10 \times S_{\text{proj}} + 0.05 \times S_{\text{ev}}$$

| Component | Weight | Description |
|-----------|--------|-------------|
| **Required Skills** | 35% | Exact and normalized match ratio of must-have skills with preferred skill bonuses. |
| **Semantic Fit** | 25% | BGE-M3 & Cross-Encoder semantic similarity between resume chunks and job requirements. |
| **Relevant Experience** | 15% | Duration and depth of candidate experience relative to minimum required years. |
| **Education** | 10% | Degree and field of study alignment. |
| **Project Relevance** | 10% | Technical stack overlap in personal/professional projects. |
| **Evidence Quality** | 5% | Direct textual evidence coverage across job description requirements. |

## Confidence Indicator

- **HIGH**: $\ge 75\%$ evidence coverage and $\ge 3$ relevant retrieved chunks.
- **MEDIUM**: $\ge 45\%$ evidence coverage.
- **LOW**: Below $45\%$ coverage or missing key section data.
