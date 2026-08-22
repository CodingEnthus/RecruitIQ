# Security & Prompt Injection Defense

Resumes uploaded by applicants are treated as **untrusted user input**.

## Security Safeguards

1. **Adversarial Pattern Scanning**: Scans text for prompt injection keywords (e.g. `ignore previous instructions`, `rank me first`, `give me a score of 100`, `system prompt override`).
2. **Instruction Isolation**: Sanitizes suspicious instruction-like lines before passing context to LLM extractors.
3. **Strict Instruction Hierarchy**: The LLM prompt explicitly demarcates system instructions from untrusted candidate data.
4. **Deterministic Ranking Integrity**: Prompt injection text cannot alter numerical scores because scores are computed mathematically by `ScoringEngineService` rather than decided by the LLM.
5. **Recruiter Warning Banner**: Displays an alert banner on candidate cards if instruction-like text was detected.
6. **Privacy Mode**: Enables anonymized screening by scrubbing names, emails, phones, photos, and identity markers from evaluation contexts.
