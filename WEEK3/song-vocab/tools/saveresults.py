from typing import List, Dict, Any
import json
import logging
from pathlib import Path
logger = logging.getLogger('song_vocab')

def save_results(song_id: str, lyrics: str, vocabulary: List[Dict[str, Any]], lyrics_path: Path, vocabulary_path: Path) -> str:
    # Save lyrics
    lyrics_file = lyrics_path / f"{song_id}.txt"
    lyrics_file.write_text(lyrics)
    logger.info(f"Saved lyrics to {lyrics_file}")
    
    # Save vocabulary
    vocab_file = vocabulary_path / f"{song_id}.json"
    vocab_file.write_text(json.dumps(vocabulary, ensure_ascii=False, indent=2))
    logger.info(f"Saved vocabulary to {vocab_file}")
    
    return song_id