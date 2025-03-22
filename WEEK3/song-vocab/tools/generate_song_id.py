import re
from typing import Dict

def generate_song_id(artist: str, title: str) -> Dict[str, str]:
    def clean_string(s: str) -> str:
        s = re.sub(r'[^\w\s-]', '', s.lower())
        return re.sub(r'[-\s]+', '-', s).strip('-')
    
    song_id = f"{clean_string(artist)}-{clean_string(title)}"
    return {"song_id": song_id}