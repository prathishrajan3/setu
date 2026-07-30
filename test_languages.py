import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('.'))

from fastapi.testclient import TestClient
from app.main import app
import app.gemma_client as gc
import tempfile

client = TestClient(app)

class MockSegment:
    def __init__(self, text):
        self.text = text

class MockInfo:
    def __init__(self, language, prob):
        self.language = language
        self.language_probability = prob

class MockWhisper:
    def __init__(self, text, lang, prob):
        self.text = text
        self.lang = lang
        self.prob = prob
        
    def transcribe(self, path):
        return [MockSegment(self.text)], MockInfo(self.lang, self.prob)

# We will patch gc.get_whisper to return our mock
original_get_whisper = gc.get_whisper

# Also mock query_gemma to just return the prompt we sent it so we can verify the routing!
def mock_query_gemma(prompt=None, image_path=None, audio_path=None, tools=None, messages=None):
    # Just return the messages to see the system prompt
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
    return {"role": "assistant", "content": f"MOCKED RESPONSE. Prompt was: {messages[0]['content']}"}

gc.query_gemma = mock_query_gemma

def run_test_text(query, expected_lang):
    print(f"--- TEXT TEST: {expected_lang} ---")
    response = client.post("/chat", data={"text": query})
    print("Response:", response.json().get("response"))
    print()

def run_test_audio(text, lang_code, expected_lang):
    print(f"--- AUDIO TEST: {expected_lang} (Whisper lang: {lang_code}) ---")
    gc.get_whisper = lambda: MockWhisper(text, lang_code, 0.99)
    
    # create dummy wav file
    fd, path = tempfile.mkstemp(suffix=".wav")
    with os.fdopen(fd, 'wb') as f:
        # just write some dummy bytes
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
        
    with open(path, "rb") as f:
        response = client.post("/chat", files={"audio": ("test.wav", f, "audio/wav")})
    
    print("Response:", response.json().get("response"))
    print()
    os.remove(path)

if __name__ == "__main__":
    print("=== TEXT PATH TESTS ===")
    run_test_text("What is a tractor?", "English")
    run_test_text("டிராக்டர் என்றால் என்ன?", "Tamil")
    run_test_text("ట్రాక్టర్ అంటే ఏమిటి?", "Telugu")
    run_test_text("ट्रैक्टर क्या है?", "Hindi")
    run_test_text("டிராக்டர் cost என்ன?", "Code-switched Tamil-English")
    run_test_text("ట్రాక్టర్ cost ఎంత?", "Code-switched Telugu-English")
    run_test_text("ट्रैक्टर cost क्या है?", "Code-switched Hindi-English")
    
    print("=== AUDIO PATH TESTS ===")
    run_test_audio("What is a tractor?", "en", "English")
    run_test_audio("டிராக்டர் என்றால் என்ன?", "ta", "Tamil")
    run_test_audio("ట్రాక్టర్ అంటే ఏమిటి?", "te", "Telugu")
    run_test_audio("ट्रैक्टर क्या है?", "hi", "Hindi")
    run_test_audio("டிராக்டர் cost என்ன?", "ta", "Code-switched Tamil-English (Audio fallback)")
    run_test_audio("ట్రాక్టర్ cost ఎంత?", "te", "Code-switched Telugu-English (Audio fallback)")
    run_test_audio("ट्रैक्टर cost क्या है?", "hi", "Code-switched Hindi-English (Audio fallback)")
    
