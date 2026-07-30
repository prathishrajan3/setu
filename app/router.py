import re

def route_dialect(text: str) -> str:
    """
    Mock MoE-inspired routing logic based on language heuristics.
    Detects if the input is Tamil, English, or Code-switched.
    In a real scenario, this would be an MoE projector for audio, 
    but since we take text transcriptions for simplicity in this hackathon,
    we route via text analysis.
    """
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    
    if len(tamil_chars) > 0 and len(english_words) > 0:
        return "code-switched"
    elif len(tamil_chars) > 0:
        return "tamil"
    else:
        return "english"

def inject_routing_prompt(text: str) -> str:
    dialect = route_dialect(text)
    if dialect == "code-switched":
        return f"[System: The following user input is code-switched Tamil-English. Provide the answer in Tamil but feel free to use English agricultural terms if clearer.]\n{text}"
    elif dialect == "tamil":
        return f"[System: The following user input is in pure Tamil. Provide the answer in Tamil.]\n{text}"
    else:
        return f"[System: The following user input is in English. Provide the answer in English.]\n{text}"
