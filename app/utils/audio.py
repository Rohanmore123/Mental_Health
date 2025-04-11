import base64
import os
import tempfile
from typing import Optional, Tuple

class AudioProcessor:
    """Utility class for processing audio files."""
    
    @staticmethod
    def decode_base64_audio(base64_audio: str, output_format: str = "wav") -> str:
        """
        Decode base64 audio string and save to a temporary file.
        
        Args:
            base64_audio: Base64 encoded audio string
            output_format: Output audio format (default: wav)
            
        Returns:
            Path to the temporary audio file
        """
        # Decode base64 string
        audio_data = base64.b64decode(base64_audio)
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f".{output_format}", delete=False
        )
        temp_file_path = temp_file.name
        
        # Write audio data to the temporary file
        with open(temp_file_path, "wb") as f:
            f.write(audio_data)
        
        return temp_file_path
    
    @staticmethod
    def encode_audio_to_base64(audio_file_path: str) -> str:
        """
        Encode an audio file to base64 string.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Base64 encoded audio string
        """
        with open(audio_file_path, "rb") as f:
            audio_data = f.read()
        
        # Encode audio data to base64
        base64_audio = base64.b64encode(audio_data).decode("utf-8")
        
        return base64_audio
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """
        Clean up a temporary file.
        
        Args:
            file_path: Path to the temporary file
        """
        if os.path.exists(file_path):
            os.remove(file_path)
