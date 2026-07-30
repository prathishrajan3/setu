import re

def route_dialect(text: str) -> str:
    """
    Heuristic MoE-inspired routing logic based on language heuristics.
    Detects if the input is Tamil, Telugu, Hindi, English, or Code-switched.
    In a real scenario, this would be an MoE projector for audio, 
    but since we take text transcriptions for simplicity in this hackathon,
    we route via text analysis.
    """
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    telugu_chars = re.findall(r'[\u0C00-\u0C7F]', text)
    hindi_chars = re.findall(r'[\u0900-\u097F]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    
    has_tamil = len(tamil_chars) > 0
    has_telugu = len(telugu_chars) > 0
    has_hindi = len(hindi_chars) > 0
    has_english = len(english_words) > 0
    
    # Determine which Indic scripts are present
    indic_scripts = []
    if has_tamil: indic_scripts.append("tamil")
    if has_telugu: indic_scripts.append("telugu")
    if has_hindi: indic_scripts.append("hindi")
    
    if len(indic_scripts) > 0 and has_english:
        # If multiple indic scripts, join them
        return f"code-switched-{'-'.join(indic_scripts)}-english"
    elif len(indic_scripts) > 0:
        # E.g. 'tamil' or 'telugu-hindi'
        return '-'.join(indic_scripts)
    elif has_english:
        return "english"
    else:
        return "unrecognized"

def inject_routing_prompt(dialect: str, text: str) -> str:
    """
    Injects the correct system instruction based on the dialect string.
    """
    if "code-switched" in dialect:
        # Extract the Indic language name, e.g. "tamil" from "code-switched-tamil-english"
        lang = dialect.replace("code-switched-", "").replace("-english", "").title()
        return f"[System: The following user input is code-switched {lang}-English. Provide the answer in {lang} but feel free to use English agricultural terms if clearer.]\n{text}"
    elif dialect == "english":
        return f"[System: The following user input is in English. Provide the answer in English.]\n{text}"
    elif dialect == "unrecognized":
        return text
    else:
        # Pure language
        lang = dialect.title()
        return f"[System: The following user input is in pure {lang}. Provide the answer in {lang}.]\n{text}"
