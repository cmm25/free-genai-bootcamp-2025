import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)


async def get_page_content(url: str) -> Dict[str, Optional[str]]:

    logger.info(f"Fetching content from URL: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug("Making HTTP request...")
            async with session.get(url) as response:
                if response.status != 200:
                    error_msg = f"Error: HTTP {response.status}"
                    logger.error(error_msg)
                    return {
                        "swahili_lyrics": None,
                        "pronunciation_guide": None,
                        "metadata": error_msg
                    }

                logger.debug("Reading response content...")
                html = await response.text()
                logger.info(
                    f"Successfully fetched page content ({len(html)} bytes)")
                return extract_lyrics_from_html(html, url)
    except Exception as e:
        error_msg = f"Error fetching page: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "swahili_lyrics": None,
            "pronunciation_guide": None,
            "metadata": error_msg
        }


def extract_lyrics_from_html(html: str, url: str) -> Dict[str, Optional[str]]:
    """
    Extract lyrics from HTML content based on common patterns in lyrics websites.
    """
    logger.info("Starting lyrics extraction from HTML")
    soup = BeautifulSoup(html, 'html.parser')

    logger.debug("Cleaning HTML content...")
    for element in soup(['script', 'style', 'header', 'footer', 'nav']):
        element.decompose()

    # Common patterns for lyrics containers
    lyrics_patterns = [
        {"class_": re.compile(r"lyrics?|maneno|nyimbo|original", re.I)},
        {"class_": re.compile(r"song-content|song-text|track-text", re.I)},
        {"id": re.compile(r"lyrics?|maneno|nyimbo|original", re.I)},
        {"class_": "lyrics_box"},
        {"class_": "swahili_text"},
        {"class_": "song_content"}
    ]

    swahili_lyrics = None
    pronunciation_guide = None
    metadata = ""
    logger.debug("Searching for lyrics containers...")

    for pattern in lyrics_patterns:
        logger.debug(f"Trying pattern: {pattern}")
        elements = soup.find_all(**pattern)
        logger.debug(f"Found {len(elements)} matching elements")

        for element in elements:
            text = clean_text(element.get_text())
            logger.debug(f"Extracted text length: {len(text)} chars")

            # Detect if text is primarily Swahili or pronunciation guide
            if is_primarily_swahili(text) and not swahili_lyrics:
                logger.info("Found Swahili lyrics")
                swahili_lyrics = text
            elif is_pronunciation_guide(text) and not pronunciation_guide:
                logger.info("Found pronunciation guide")
                pronunciation_guide = text

    # If no structured containers found, try to find the largest text block
    if not swahili_lyrics and not pronunciation_guide:
        logger.info(
            "No lyrics found in structured containers, trying fallback method")
        text_blocks = [clean_text(p.get_text()) for p in soup.find_all('p')]
        if text_blocks:
            largest_block = max(text_blocks, key=len)
            logger.debug(
                f"Found largest text block: {len(largest_block)} chars")

            if is_primarily_swahili(largest_block):
                logger.info("Largest block contains Swahili text")
                swahili_lyrics = largest_block
            elif is_pronunciation_guide(largest_block):
                logger.info("Largest block contains pronunciation guide")
                pronunciation_guide = largest_block

    result = {
        "swahili_lyrics": swahili_lyrics,
        "pronunciation_guide": pronunciation_guide,
        "metadata": metadata or "Lyrics extracted successfully"
    }

    # Log the results
    if swahili_lyrics:
        logger.info(f"Found Swahili lyrics ({len(swahili_lyrics)} chars)")
    if pronunciation_guide:
        logger.info(
            f"Found pronunciation guide ({len(pronunciation_guide)} chars)")

    return result


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and unnecessary characters.
    """
    logger.debug(f"Cleaning text of length {len(text)}")
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    result = text.strip()
    logger.debug(f"Text cleaned, new length: {len(result)}")
    return result


def is_primarily_swahili(text: str) -> bool:
    """
    Check if text contains primarily Swahili characters.
    """
    swahili_markers = ['na', 'kwa', 'ya', 'wa', 'ni', 'si', 'ndio', 'hapana']

    marker_count = sum(
        1 for word in swahili_markers if word in text.lower().split())

    swahili_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = len(text.strip())
    ratio = swahili_chars / total_chars if total_chars > 0 else 0
    logger.debug(
        f"Swahili character ratio: {ratio:.2f} ({swahili_chars}/{total_chars})")

    return (marker_count > 0) or (swahili_chars > 0 and ratio > 0.3)


def is_pronunciation_guide(text: str) -> bool:
    """
    Check if text is likely a pronunciation guide.
    """
    phonetic_markers = ['(', ')', '[', ']', ':', '·', '-']
    has_markers = any(marker in text for marker in phonetic_markers)

    special_notation_count = sum(
        1 for char in text if char in phonetic_markers)
    special_ratio = special_notation_count / len(text) if len(text) > 0 else 0
    logger.debug(f"Pronunciation notation ratio: {special_ratio:.2f}")

    return has_markers and special_ratio > 0.05
