import pymupdf as fitz
import re
from typing import Dict, Tuple

class PDFParserService:
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str) -> Tuple[str, Dict[str, str]]:
        if filename.lower().endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="ignore")
        elif filename.lower().endswith(".pdf"):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_lines = []
            for page in doc:
                text_lines.append(page.get_text())
            text = "\n".join(text_lines)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")

        cleaned_text = PDFParserService._clean_text(text)
        sections = PDFParserService._split_sections(cleaned_text)
        return cleaned_text, sections

    @staticmethod
    def _clean_text(text: str) -> str:
        # Normalize whitespace while preserving line structure
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\t', ' ', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def _split_sections(text: str) -> Dict[str, str]:
        sections = {
            "summary": "",
            "skills": "",
            "experience": "",
            "education": "",
            "projects": "",
            "certifications": ""
        }
        
        lines = text.split('\n')
        current_section = "summary"
        section_content = {sec: [] for sec in sections.keys()}

        # Enhanced section header patterns to capture uppercase, degree names, academic titles, key projects, etc.
        section_headers = {
            "skills": [
                r"^(technical\s+)?skills", r"^core\s+competencies", r"^technologies",
                r"^programming\s+languages", r"^tech\s+stack"
            ],
            "experience": [
                r"^(work\s+|professional\s+|relevant\s+)?experience", r"^employment(\s+history)?",
                r"^work\s+history", r"^internships?", r"^practical\s+experience"
            ],
            "education": [
                r"^education(\s+and\s+qualifications)?", r"^academic(\s+background|\s+qualifications)?",
                r"^qualifications", r"^academic\s+details"
            ],

            "projects": [
                r"^(key\s+|academic\s+|personal\s+|major\s+)?projects", r"^projects\s+handled",
                r"^portfolio", r"^selected\ obligation\ projects"
            ],
            "certifications": [
                r"^certifications?", r"^licenses(\s+&\s+certifications)?", r"^credentials",
                r"^courses(\s+&\s+workshops)?"
            ]
        }

        for line in lines:
            line_clean = line.strip().lower()
            if not line_clean:
                continue

            # Remove leading bullet symbols like -, *, •
            line_normalized = re.sub(r'^[\s\-*•\d\.]+\s*', '', line_clean)

            matched_new_section = False
            for sec_key, patterns in section_headers.items():
                for pat in patterns:
                    # Match standalone header lines or line matching section regex
                    if re.match(pat, line_normalized):
                        current_section = sec_key
                        matched_new_section = True
                        break
                if matched_new_section:
                    break

            if not matched_new_section:
                section_content[current_section].append(line)

        for sec_key in sections.keys():
            sections[sec_key] = "\n".join(section_content[sec_key]).strip()

        return sections
