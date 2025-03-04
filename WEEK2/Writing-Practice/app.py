import streamlit as st
import requests
from enum import Enum
import json
from typing import Optional, List, Dict
import openai
import logging
import random
import pandas as pd

logger = logging.getLogger('swahili_learning_app')
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

fh = logging.FileHandler('swahili_app.log')
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - SWAHILI_LEARNING_APP - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)

# Prevent propagation to root logger
logger.propagate = False


class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"


class SwahiliLearningApp:
    def __init__(self):
        logger.debug("Initializing Swahili Learning App...")
        st.set_page_config(
            page_title="Swahili Learning Portal",
            page_icon="📚",
            layout="wide"
        )
        self.initialize_session_state()
        self.load_vocabulary()
        self.setup_sidebar()

    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state.current_sentence = ""
        if 'review_data' not in st.session_state:
            st.session_state.review_data = None
        if 'practice_count' not in st.session_state:
            st.session_state.practice_count = 0
        if 'nav_selection' not in st.session_state:
            st.session_state.nav_selection = "🏠 Dashboard"

    def setup_sidebar(self):
        with st.sidebar:
            st.title("Learning Portal")
            st.markdown("---")

            st.subheader("📍 Navigation")
            if 'nav_selection' not in st.session_state:
                st.session_state.nav_selection = "🏠 Dashboard"

            st.session_state.nav_selection = st.radio(
                "Choose Section:",
                ["🏠 Dashboard", "📝 Writing Practice", "📊 Progress", "ℹ️ Help"],
                key="nav_radio"
            )

            st.markdown("---")

            st.subheader("📈 Session Stats")
            if self.vocabulary:
                st.metric("Words Available", len(
                    self.vocabulary.get('words', [])))
                st.metric("Practice Sessions", st.session_state.practice_count)

            st.markdown("---")

            # Group Info
            if self.vocabulary:
                st.subheader("📚 Current Group")
                st.info(
                    f"Studying: {self.vocabulary.get('group_name', 'Unknown Group')}")

    def load_vocabulary(self):
        """Fetch vocabulary from API using group_id from query parameters"""
        try:
            group_id = st.query_params.get('group_id', '')

            st.write(f"Debug - Query Parameters: {st.query_params}")
            st.write(f"Debug - Group ID: {group_id}")

            if not group_id:
                st.error("No group_id provided in query parameters")
                self.vocabulary = None
                return

            base_url = "http://localhost:8000"
            url = f'{base_url}/api/groups/{group_id}/words/'

            st.write(f"Debug - Attempting to fetch from: {url}")

            # Add headers for authentication
            headers = {
                'Accept': 'application/json',
                # 'Authorization': f'Token {self.get_auth_token()}'
            }

            try:
                response = requests.get(url, headers=headers)
                st.write(f"Debug - Response Status: {response.status_code}")
                st.write(f"Debug - Response Headers: {dict(response.headers)}")
                st.write(f"Debug - Response Content: {response.text[:200]}")

                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        st.error("Empty response data")
                        self.vocabulary = None
                        return

                    self.vocabulary = {
                        'words': data,
                        'group_name': f'Group {group_id}'
                    }
                    st.success(
                        f"Successfully loaded vocabulary for group {group_id}")
                elif response.status_code == 401:
                    st.error(
                        "Authentication failed. Please check your API credentials.")
                    self.vocabulary = None
                elif response.status_code == 404:
                    st.error(f"Vocabulary group with ID {group_id} not found")
                    self.vocabulary = None
                else:
                    st.error(
                        f"Failed to fetch vocabulary. Status code: {response.status_code}")
                    self.vocabulary = None

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the API server. Please make sure it's running at http://localhost:8000")
                self.vocabulary = None
            except requests.exceptions.JSONDecodeError as e:
                st.error(f"Invalid JSON response: {str(e)}")
                self.vocabulary = None

        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.write(f"Debug - Exception details: {str(e)}")
            self.vocabulary = None

    def generate_sentence(self, word: dict) -> str:
        """Generate a sentence using OpenAI API"""
        swahili_word = word.get('swahili', '')

        prompt = f"""Generate a simple Swahili sentence using the word '{swahili_word}'.
        The grammar should be appropriate for beginner Swahili learners.
        Use basic sentence structures that demonstrate:
        - Subject-Verb-Object order
        - Simple present tense
        - Common vocabulary related to daily life
        
        Please provide the response in this format:
        Swahili: [sentence in Swahili]
        English: [English translation]
        
        Important: Ensure the sentence is grammatically correct in Swahili and provides context for the word."""

        logger.debug(f"Generating sentence for word: {swahili_word}")
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def grade_submission(self, text_input: str) -> Dict:
        """Process text submission and grade it"""
        # For now using static response, in a real app this would analyze the text
        return {
            "transcription": text_input,
            "translation": "I am eating lunch.",  # In real app, would translate the input
            "grade": "A",
            "feedback": "Excellent Swahili sentence! Your writing shows good understanding of basic sentence structure."
        }

    def render_dashboard(self):
        """Render the dashboard view"""
        st.title("🏠 Swahili Learning Dashboard")

        if not self.vocabulary:
            st.warning("Please select a vocabulary group to start learning.")
            return

        # Create three columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📝 Quick Start")
            if st.button("Start Writing Practice"):
                st.session_state.app_state = AppState.PRACTICE
                st.experimental_rerun()

        with col2:
            st.subheader("🎯 Today's Goals")
            st.info("Complete 5 writing exercises")
            st.progress(min(st.session_state.practice_count / 5, 1.0))

        with col3:
            st.subheader("🌟 Achievement")
            st.success(
                f"Current Streak: {st.session_state.practice_count} exercises")

        # Available Words
        st.subheader("📚 Available Words")
        if self.vocabulary and self.vocabulary.get('words'):
            words_df = pd.DataFrame(self.vocabulary['words'])
            st.dataframe(
                words_df[['Swahili', 'English', 'Pronounciation']],
                hide_index=True,
                use_container_width=True
            )

    def render_practice_state(self):
        """Render the practice state UI"""
        st.title("📝 Swahili Writing Practice")

        if not self.vocabulary:
            st.warning("Please select a vocabulary group to start practice.")
            return

        if st.session_state.current_sentence:
            st.markdown("### 📝 Writing Task")
            st.info(st.session_state.current_sentence)

            user_input = st.text_area(
                "Type your Swahili sentence here:",
                height=100,
                key="swahili_input",
                help="Write your sentence using the word provided above."
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("Submit for Review", type="primary"):
                    if user_input:
                        st.session_state.review_data = self.grade_submission(
                            user_input)
                        st.session_state.app_state = AppState.REVIEW
                        st.experimental_rerun()
            with col2:
                if st.button("Clear Input"):
                    st.session_state.current_sentence = ""
                    st.experimental_rerun()
        else:
            st.markdown("### 🎯 Generate New Task")
            if st.button("Generate New Sentence", type="primary"):
                if not self.vocabulary.get('words'):
                    st.error("No words found in the vocabulary group")
                    return

                word = random.choice(self.vocabulary['words'])
                sentence = self.generate_sentence(word)
                st.session_state.current_sentence = sentence
                st.experimental_rerun()

    def render_review_state(self):
        """Render the review state UI"""
        st.title("📋 Review Your Writing")

        if not st.session_state.review_data:
            st.warning("No review data available.")
            return

        st.markdown("### Original Task")
        st.info(st.session_state.current_sentence)

        st.markdown("### Your Submission")
        review_data = st.session_state.review_data

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Your Text")
            st.write(review_data['transcription'])

        with col2:
            st.markdown("#### Translation")
            st.write(review_data['translation'])

        st.markdown("### Feedback")
        st.markdown(f"**Feedback:** {review_data['feedback']}")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Next Question", type="primary"):
                st.session_state.practice_count += 1
                st.session_state.app_state = AppState.SETUP
                st.session_state.current_sentence = ""
                st.session_state.review_data = None
                st.experimental_rerun()

    def render_progress(self):
        """Render the progress tracking view"""
        st.title("📊 Learning Progress")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Practice Sessions",
                        st.session_state.practice_count)
        with col2:
            st.metric("Words Practiced", len(self.vocabulary.get(
                'words', [])) if self.vocabulary else 0)

        # Progress chart
        st.subheader("Learning Journey")
        chart_data = pd.DataFrame({
            'Sessions': range(1, st.session_state.practice_count + 1),
            'Words': range(1, st.session_state.practice_count + 1)
        })
        st.line_chart(chart_data.set_index('Sessions'))

    def render_help(self):
        """Render the help and information view"""
        st.title("ℹ️ Help & Information")

        st.markdown("""
        ### 🌟 Welcome to Swahili Learning Portal!
        
        This platform helps you practice and improve your Swahili writing skills.
        
        #### 📝 How to Use
        1. Select a vocabulary group from the sidebar
        2. Generate a new writing task
        3. Write your response in Swahili
        4. Submit for instant feedback
        
        #### 🎯 Features
        - Writing practice with real-time feedback
        - Progress tracking
        - Vocabulary management
        - Performance analytics
        
        #### 💡 Tips
        - Practice regularly for better results
        - Review your previous submissions
        - Pay attention to grammar and spelling
        """)

    def run(self):
        """Main app loop"""
        if st.session_state.nav_selection == "🏠 Dashboard":
            self.render_dashboard()
        elif st.session_state.nav_selection == "📝 Writing Practice":
            if st.session_state.app_state == AppState.REVIEW:
                self.render_review_state()
            else:
                self.render_practice_state()
        elif st.session_state.nav_selection == "📊 Progress":
            self.render_progress()
        elif st.session_state.nav_selection == "ℹ️ Help":
            self.render_help()


# Run the app
if __name__ == "__main__":
    app = SwahiliLearningApp()
    app.run()
