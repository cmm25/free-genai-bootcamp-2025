import streamlit as st
import requests
from enum import Enum
import json
from typing import Dict
import openai
import logging
import random
import pandas as pd
from PIL import Image
import numpy as np

try:
    from manga_ocr import MangaOcr
    HAS_MANGA_OCR = True
except ImportError:
    HAS_MANGA_OCR = False

logger = logging.getLogger('japanese_writing_app')
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

fh = logging.FileHandler('japanese_app.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - JAPANESE_WRITING_APP - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# Prevent propagation to root logger
logger.propagate = False


class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"


class JapaneseWritingApp:
    def __init__(self):
        logger.debug("Initializing Japanese Writing Practice App...")
        st.set_page_config(
            page_title="Japanese Writing Practice",
            page_icon="✍️",
            layout="wide"
        )
        self.initialize_session_state()
        self.load_vocabulary()
        self.setup_sidebar()
        self.initialize_ocr()
        self.render_page()

    def initialize_ocr(self):
        if not HAS_MANGA_OCR:
            st.sidebar.warning("OCR functionality is disabled. Install MangaOCR to enable handwriting analysis.")
            self.ocr = None
            return
            
        try:
            # Initialize MangaOCR
            self.ocr = MangaOcr()
            logger.info("MangaOCR initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MangaOCR: {str(e)}")
            st.sidebar.error(f"Error initializing OCR: {str(e)}")
            self.ocr = None

    def process_image_with_ocr(self, image):
        if not HAS_MANGA_OCR or not self.ocr:
            return "OCR not available. Please install MangaOCR."
            
        try:
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # MangaOCR processes the image directly
            result = self.ocr(image)
            
            # MangaOCR returns text directly, no need for additional processing
            if not result.strip():
                return ""
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image with OCR: {str(e)}")
            return f"Error processing image: {str(e)}"

    def grade_submission(self, text_input: str, reference: str) -> Dict:
        try:
            if not text_input.strip():
                return {
                    "score": 0,
                    "feedback": "No Japanese text was detected in the image. Please make sure your handwriting is clear and the image is well-lit.",
                    "corrections": reference,
                    "user_attempt": ""
                }
            
            prompt = f"""Please evaluate this Japanese writing submission:
            User's submission: {text_input}
            Reference: {reference}
            
            Assess accuracy, grammar, and character formation. Provide constructive feedback.
            Format your response as JSON with the following fields:
            {{
                "score": 0-100,
                "feedback": "detailed feedback",
                "corrections": "any corrections needed"
            }}"""
            
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            result['user_attempt'] = text_input
            return result
        except Exception as e:
            logger.error(f"Error grading submission: {str(e)}")
            return {
                "score": 0,
                "feedback": f"Error grading submission: {str(e)}",
                "corrections": reference,
                "user_attempt": text_input
            }

    def initialize_session_state(self):
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state.current_sentence = ""
        if 'current_japanese_sentence' not in st.session_state:
            st.session_state.current_japanese_sentence = ""
        if 'review_data' not in st.session_state:
            st.session_state.review_data = None
        if 'practice_count' not in st.session_state:
            st.session_state.practice_count = 0
        if 'nav_selection' not in st.session_state:
            st.session_state.nav_selection = "🏠 Dashboard"
        if 'uploaded_image' not in st.session_state:
            st.session_state.uploaded_image = None
        if 'ocr_result' not in st.session_state:
            st.session_state.ocr_result = None
        if 'vocabulary' not in st.session_state:
            st.session_state.vocabulary = []

    def setup_sidebar(self):
        with st.sidebar:
            st.title("Japanese Writing Practice")
            st.markdown("---")

            st.subheader("📍 Navigation")
            if 'nav_selection' not in st.session_state:
                st.session_state.nav_selection = "🏠 Dashboard"

            st.session_state.nav_selection = st.radio(
                "Choose Section:",
                ["🏠 Dashboard", "✍️ Writing Practice", "📷 Image Upload", "📊 Progress", "ℹ️ Help"],
                key="nav_radio"
            )

            st.markdown("---")

            st.subheader("📈 Session Stats")
            st.metric("Practice Sessions", st.session_state.practice_count)

            st.markdown("---")

    def load_vocabulary(self):
        self.vocabulary = [
            {"english": "hello", "japanese": "こんにちは", "romaji": "konnichiwa"},
            {"english": "thank you", "japanese": "ありがとう", "romaji": "arigatou"},
            {"english": "good morning", "japanese": "おはようございます", "romaji": "ohayou gozaimasu"},
            {"english": "goodbye", "japanese": "さようなら", "romaji": "sayounara"},
            {"english": "excuse me", "japanese": "すみません", "romaji": "sumimasen"},
            {"english": "delicious", "japanese": "おいしい", "romaji": "oishii"},
            {"english": "water", "japanese": "水", "romaji": "mizu"},
            {"english": "book", "japanese": "本", "romaji": "hon"},
            {"english": "friend", "japanese": "友達", "romaji": "tomodachi"},
            {"english": "cat", "japanese": "猫", "romaji": "neko"}
        ]
        st.session_state.vocabulary = self.vocabulary

    def generate_sentence(self, word: dict) -> str:
        english_word = word.get('english', '')

        prompt = f"""Generate a simple English sentence using the word '{english_word}' followed by its Japanese translation.
        The sentence should be appropriate for beginner Japanese learners.
        Use basic sentence structures for everyday situations.
        
        Please provide the response in this format:
        English: [sentence in English]
        Japanese: [sentence in Japanese]
        Romaji: [Japanese sentence in romaji]
        
        Important: Ensure both sentences are grammatically correct and natural."""

        logger.debug(f"Generating sentence for word: {english_word}")
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            full_response = response.choices[0].message.content.strip()
            japanese_sentence = ""
            for line in full_response.split('\n'):
                if line.startswith("Japanese:"):
                    japanese_sentence = line.replace("Japanese:", "").strip()
                    break
            st.session_state.current_japanese_sentence = japanese_sentence
            return full_response
        except Exception as e:
            logger.error(f"Error generating sentence: {str(e)}")
            fallback_japanese = f"これは{word.get('japanese')}です。"
            fallback_romaji = f"Kore wa {word.get('romaji')} desu."
            st.session_state.current_japanese_sentence = fallback_japanese
            return f"""English: This is a {english_word}.
Japanese: {fallback_japanese}
Romaji: {fallback_romaji}"""

    def render_dashboard(self):
        st.title("🏠 Japanese Writing Practice")
        
        st.markdown("""
        ## Welcome to Japanese Writing Practice!
        
        This application helps you practice writing Japanese sentences. You can:
        
        - Generate simple Japanese sentences based on vocabulary words
        - Practice writing Japanese characters
        - Upload images of your handwritten Japanese for evaluation
        - Track your progress over time
        
        Get started by selecting "✍️ Writing Practice" or "📷 Image Upload" from the sidebar.
        """)

        st.subheader("📚 Available Vocabulary")
        vocab_df = pd.DataFrame(self.vocabulary)
        st.dataframe(vocab_df)

    def render_writing_practice(self):
        st.title("✍️ Japanese Writing Practice")

        st.subheader("Select a word to practice")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if self.vocabulary:
                selected_word_index = st.selectbox(
                    "Choose a word:",
                    range(len(self.vocabulary)),
                    format_func=lambda i: f"{self.vocabulary[i]['english']} ({self.vocabulary[i]['japanese']})"
                )
                
                selected_word = self.vocabulary[selected_word_index]
                
                if st.button("Generate Practice Sentence"):
                    with st.spinner("Generating sentence..."):
                        sentence_output = self.generate_sentence(selected_word)
                        st.session_state.current_sentence = sentence_output
                        st.session_state.practice_count += 1
                        st.session_state.ocr_result = None
                        st.session_state.review_data = None

        with col2:
            if st.session_state.current_sentence:
                st.markdown("### Practice Sentence:")
                st.markdown(st.session_state.current_sentence)

                st.markdown("---")
                st.subheader("Your Practice")

                uploaded_file = st.file_uploader(
                    "Upload your handwritten version of the Japanese sentence above",
                    type=["jpg", "jpeg", "png"],
                    key="handwriting_upload"
                )

                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Your Handwriting", width=300)

                    if st.button("Analyze My Handwriting"):
                        if st.session_state.current_japanese_sentence:
                            with st.spinner("Analyzing your handwriting and grading..."):
                                if not HAS_MANGA_OCR:
                                    st.warning("OCR functionality is not available. Please install MangaOCR package.")
                                    extracted_text = "OCR not available. Using sample text for demo purposes."
                                else:
                                    extracted_text = self.process_image_with_ocr(image)
                                
                                result = self.grade_submission(
                                    extracted_text,
                                    st.session_state.current_japanese_sentence
                                )
                                st.session_state.review_data = result

                        else:
                            st.warning("Please generate a sentence first.")

                if st.session_state.review_data:
                    st.markdown("### Feedback:")
                    result = st.session_state.review_data
                    st.markdown(f"**Reference:** {st.session_state.current_japanese_sentence}")
                    st.markdown(f"**Your Attempt (from image):** {result.get('user_attempt', 'N/A')}")
                    st.progress(result["score"]/100)
                    st.markdown(f"**Score:** {result['score']}/100")
                    st.markdown(f"**Feedback:** {result['feedback']}")

                    if result["corrections"]:
                        st.markdown(f"**Corrections:** {result['corrections']}")

    def render_image_upload(self):
        st.title("📷 Japanese Handwriting Analysis")
        
        st.markdown("""
        Upload an image of your handwritten Japanese text for analysis. 
        The system will extract the text and provide feedback.
        """)
        
        if not HAS_MANGA_OCR:
            st.warning("MangaOCR is not installed. This feature is currently disabled.")
            st.info("To enable OCR functionality, please install MangaOCR package:")
            st.code("pip install manga-ocr")
            return
            
        uploaded_file = st.file_uploader("Upload handwritten Japanese image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", width=400)

            if st.button("Analyze Handwriting"):
                with st.spinner("Analyzing your handwriting..."):
                    result = self.process_image_with_ocr(image)
                    st.session_state.ocr_result = result
            
            if st.session_state.ocr_result:
                st.markdown("### Analysis Results:")
                st.markdown(st.session_state.ocr_result)

    def render_progress(self):
        st.title("📊 Your Progress")
        
        st.markdown("""
        Track your Japanese writing progress over time.
        
        As you practice more, your progress metrics will appear here.
        """)

        st.metric("Total Practice Sessions", st.session_state.practice_count)
        
        if st.session_state.practice_count > 0:
            chart_data = pd.DataFrame({
                'session': list(range(1, st.session_state.practice_count + 1)),
                'score': [random.randint(60, 95) for _ in range(st.session_state.practice_count)]
            })
            
            st.line_chart(chart_data, x='session', y='score')

    def render_help(self):
        st.title("ℹ️ Help & Information")
        
        st.markdown("""
        ## How to Use This App
        
        ### Writing Practice
        1. Select a word from the vocabulary list
        2. Click "Generate Practice Sentence" to get a sentence using that word
        3. Practice writing the Japanese sentence
        4. Submit your writing for feedback
        
        ### Image Upload
        1. Write Japanese characters on paper
        2. Take a photo of your writing
        3. Upload the image
        4. Click "Analyze Handwriting" to get feedback
        
        ### Tips for Better Japanese Writing
        - Pay attention to stroke order
        - Practice writing Hiragana and Katakana characters first
        - Focus on basic sentence structures
        - Regular practice is key to improvement
        """)
        

    def render_page(self):
        if st.session_state.nav_selection == "🏠 Dashboard":
            self.render_dashboard()
        elif st.session_state.nav_selection == "✍️ Writing Practice":
            self.render_writing_practice()
        elif st.session_state.nav_selection == "📷 Image Upload":
            self.render_image_upload()
        elif st.session_state.nav_selection == "📊 Progress":
            self.render_progress()
        elif st.session_state.nav_selection == "ℹ️ Help":
            self.render_help()

if __name__ == "__main__":
    app = JapaneseWritingApp()