import re
from app.schemas.candidate import CandidateProfile

class AnonymizerService:
    @staticmethod
    def anonymize_profile(profile: CandidateProfile, candidate_id: str) -> CandidateProfile:
        # Create an anonymized clone of the candidate profile
        anon_dict = profile.model_dump()
        
        # Replace identity attributes with generic masked identifiers
        anon_id = f"Candidate-{candidate_id[:8]}"
        anon_dict["name"] = anon_id
        anon_dict["email"] = "[REDACTED]"
        anon_dict["phone"] = "[REDACTED]"
        
        # Clean identity indicators from summary if present
        if anon_dict.get("summary"):
            summary = anon_dict["summary"]
            # Redact email addresses and phones
            summary = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED EMAIL]', summary)
            summary = re.sub(r'\+?\d[\d -]{8,}\d', '[REDACTED PHONE]', summary)
            anon_dict["summary"] = summary

        return CandidateProfile(**anon_dict)
