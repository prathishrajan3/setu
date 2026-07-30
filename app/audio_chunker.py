from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def chunk_audio_cif_inspired(audio_path: str, output_dir: str = "temp_chunks"):
    """
    Heuristic adaptation of CIF (Continuous Integrate-and-Fire) principle.
    Instead of fixed window (e.g., 5 seconds), it chunks audio based on acoustic content (silence).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        sound = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return []
        
    # Split on silence
    chunks = split_on_silence(
        sound,
        min_silence_len=500, # 500ms
        silence_thresh=sound.dBFS - 14,
        keep_silence=250
    )
    
    chunk_paths = []
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(output_dir, f"chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        chunk_paths.append(chunk_path)
        
    return chunk_paths
