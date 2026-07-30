import os
import wave
import struct
import math

def get_rms(data, sampwidth):
    if sampwidth == 2:
        fmt = f"<{len(data)//2}h"
        samples = struct.unpack(fmt, data)
    else:
        samples = [b for b in data]
    sum_squares = sum((s ** 2) for s in samples)
    return math.sqrt(sum_squares / len(samples)) if samples else 0

def chunk_audio_cif_inspired(audio_path: str, output_dir: str = "temp_chunks"):
    """
    Pure Python CIF-inspired chunker. Slices audio at silence boundaries 
    (content-aware) to maintain robustness for ASR without needing ffmpeg.
    Assumes standard 16-bit PCM WAV.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        with wave.open(audio_path, 'rb') as wav:
            n_channels = wav.getnchannels()
            sampwidth = wav.getsampwidth()
            framerate = wav.getframerate()
            
            chunk_duration_ms = 100
            
            chunks = []
            current_chunk = bytearray()
            
            while True:
                frames_to_read = int(framerate * chunk_duration_ms / 1000)
                data = wav.readframes(frames_to_read)
                if not data:
                    break
                
                rms = get_rms(data, sampwidth)
                is_silence = rms < 1000 # Heuristic silence threshold
                
                # Split if silent and the current chunk is at least 2 seconds long
                if is_silence and len(current_chunk) > framerate * sampwidth * n_channels * 2:
                    chunks.append(current_chunk)
                    current_chunk = bytearray()
                else:
                    current_chunk.extend(data)
                    
            if current_chunk:
                chunks.append(current_chunk)
                
            chunk_paths = []
            for i, chunk_data in enumerate(chunks):
                path = os.path.join(output_dir, f"chunk_{i}.wav")
                with wave.open(path, 'wb') as out_wav:
                    out_wav.setnchannels(n_channels)
                    out_wav.setsampwidth(sampwidth)
                    out_wav.setframerate(framerate)
                    out_wav.writeframes(chunk_data)
                chunk_paths.append(path)
                
            return chunk_paths
    except Exception as e:
        print(f"Error in pure python chunker: {e}")
        # Fallback to returning the whole file if parsing fails
        return [audio_path]
