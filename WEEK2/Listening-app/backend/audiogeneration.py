import json
import os
from typing import Dict, List, Tuple
import tempfile
import subprocess
from datetime import datetime
import torch
from transformers import (
    AutoProcessor,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    set_seed,
    SpeechT5Processor,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan,
)
import numpy as np
import soundfile as sf
import re

# Add this line to check transformers version
from transformers import __version__ as transformers_version
print(f"Transformers version: {transformers_version}")


class AudioGenerator:
    def __init__(self):
        # Initialize TTS models from Hugging Face
        self.tts_models = {
            "mms": {
                "male": "facebook/mms-tts",
                "female": "facebook/mms-tts",
                "announcer": "facebook/mms-tts",
            },
            "speecht5": {
                "male": "microsoft/speecht5_tts",
                "female": "microsoft/speecht5_tts",
                "announcer": "microsoft/speecht5_tts",
            },
        }

        self.mms_speakers = {"male": "SW_3", "female": "SW_1", "announcer": "SW_2"}

        self.tts_services = ["mms", "speecht5"]
        self.current_service_index = 0

        self.audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "backend/static/audio",
        )
        os.makedirs(self.audio_dir, exist_ok=True)

        set_seed(42)

        self.loaded_models = {}
        self.loaded_processors = {}

        # Load text generation model
        self.text_model_name = "google/mt5-small"
        self.text_tokenizer = None
        self.text_model = None

        # Speaker embeddings for SpeechT5
        self.speaker_embeddings = None

    def _load_text_model(self):
        """Load the text generation model for conversation parsing"""
        if self.text_model is None:
            print("Loading text generation model...")
            self.text_tokenizer = AutoTokenizer.from_pretrained(
                self.text_model_name)
            self.text_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.text_model_name)
            print("Text generation model loaded")

    def _generate_conversation_format(self, question: Dict) -> str:
        """Generate conversation format using local model instead of Bedrock"""
        self._load_text_model()

        # Create a prompt for the model
        prompt = f"""
        Format this Swahili question for audio generation.

        Format each part like this:
        Speaker: [name] (Gender: male/female)
        Text: [Swahili text]
        ---

        Start with:
        Speaker: Announcer (Gender: male)
        Text: Sikiliza mazungumzo yafuatayo kisha ujibu maswali.

        Question: {json.dumps(question, ensure_ascii=False)}
        """

        # Tokenize and generate
        inputs = self.text_tokenizer(
            prompt, return_tensors="pt", max_length=1024, truncation=True)
        outputs = self.text_model.generate(
            inputs.input_ids,
            max_length=1024,
            num_beams=4,
            early_stopping=True
        )
        response = self.text_tokenizer.decode(
            outputs[0], skip_special_tokens=True)

        return response

    def _create_default_conversation(self, question: Dict) -> List[Tuple[str, str, str]]:
        """Create a default conversation structure when generation fails"""
        parts = []

        # Add announcer intro
        parts.append(
            ("Announcer", "Sikiliza mazungumzo yafuatayo kisha ujibu maswali.", "male"))

        # Extract conversation if available
        if "Conversation" in question:
            # Split conversation into parts
            conversation = question["Conversation"]
            lines = conversation.split("\n")

            speaker_gender = {"Speaker1": "male", "Speaker2": "female"}
            current_speaker = "Speaker1"

            for line in lines:
                line = line.strip()
                if line:
                    parts.append(
                        (current_speaker, line, speaker_gender[current_speaker]))
                    # Alternate speakers
                    current_speaker = "Speaker2" if current_speaker == "Speaker1" else "Speaker1"

        # Add question
        if "Question" in question:
            parts.append(("Announcer", question["Question"], "male"))

        return parts

    def validate_conversation_parts(self, parts: List[Tuple[str, str, str]]) -> bool:
        """
        Validate that the conversation parts are properly formatted.
        Returns True if valid, False otherwise.
        """
        if not parts:
            print("Error: No conversation parts generated")
            return False

        # announcer for intro
        if not parts[0][0].lower() == "announcer":
            print("Error: First speaker must be Announcer")
            return False

        # Check that each part has valid content
        for i, (speaker, text, gender) in enumerate(parts):
            # Check speaker
            if not speaker or not isinstance(speaker, str):
                print(f"Error: Invalid speaker in part {i+1}")
                return False

            # Check text
            if not text or not isinstance(text, str):
                print(f"Error: Invalid text in part {i+1}")
                return False

            # Check gender
            if gender not in ["male", "female"]:
                print(f"Error: Invalid gender in part {i+1}: {gender}")
                return False

            # Check text contains some content
            if len(text.strip()) < 3:
                print(f"Error: Text too short in part {i+1}")
                return False

        return True

    def parse_conversation(self, question: Dict) -> List[Tuple[str, str, str]]:
        """
        Convert question into a format for audio generation.
        Returns a list of (speaker, text, gender) tuples.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Generate conversation format using local model
                response = self._generate_conversation_format(question)

                # Parse the response into speaker parts
                parts = []
                current_speaker = None
                current_gender = None
                current_text = None

                # Track speakers to maintain consistent gender
                speaker_genders = {}

                for line in response.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("Speaker:"):
                        # Save previous speaker's part if exists
                        if current_speaker and current_text:
                            parts.append(
                                (current_speaker, current_text, current_gender))

                        # Parse new speaker and gender
                        try:
                            speaker_part = line.split("Speaker:")[1].strip()
                            current_speaker = speaker_part.split(
                                "(")[0].strip()

                            # Extract gender if specified
                            if "Gender:" in speaker_part:
                                gender_part = speaker_part.split("Gender:")[1].split(")")[
                                    0].strip().lower()
                                if "male" in gender_part and not "female" in gender_part:
                                    current_gender = "male"
                                elif "female" in gender_part:
                                    current_gender = "female"
                                else:
                                    # Default to male if unclear
                                    current_gender = "male"
                            else:
                                # Infer gender from speaker name
                                if any(female_term in current_speaker.lower() for female_term in ["woman", "girl", "lady", "female"]):
                                    current_gender = "female"
                                else:
                                    current_gender = "male"

                            # Check for gender consistency
                            if current_speaker in speaker_genders:
                                current_gender = speaker_genders[current_speaker]
                            else:
                                speaker_genders[current_speaker] = current_gender
                        except Exception as e:
                            print(f"Error parsing speaker/gender: {line}")
                            raise e

                    elif line.startswith("Text:"):
                        current_text = line.split("Text:")[1].strip()

                    elif line == "---" and current_speaker and current_text:
                        parts.append(
                            (current_speaker, current_text, current_gender))
                        current_speaker = None
                        current_gender = None
                        current_text = None

                # Add final part if exists
                if current_speaker and current_text:
                    parts.append(
                        (current_speaker, current_text, current_gender))

                # Validate the parsed parts
                if self.validate_conversation_parts(parts):
                    return parts

                print(
                    f"Attempt {attempt + 1}: Invalid conversation format, retrying...")

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    print("Using default conversation structure")
                    return self._create_default_conversation(question)

        # If all attempts fail, use default structure
        print("Failed to generate valid conversation format, using default")
        return self._create_default_conversation(question)

    def _load_model(self, service: str, voice_type: str):
        """Load a model if not already loaded"""
        model_key = f"{service}_{voice_type}"
        if model_key not in self.loaded_models:
            model_name = self.tts_models[service][voice_type]

            if service == "mms":
                try:
                    # Try direct import for newer transformers versions
                    from transformers import AutoModelForTextToSpeech
                    self.loaded_processors[model_key] = AutoProcessor.from_pretrained(
                        model_name)
                    self.loaded_models[model_key] = AutoModelForTextToSpeech.from_pretrained(
                        model_name)
                except ImportError:
                    # Fallback to SpeechT5 if MMS isn't available
                    print("MMS not available, falling back to SpeechT5")
                    service = "speecht5"
                    model_name = self.tts_models["speecht5"][voice_type]
                    self.loaded_processors[model_key] = SpeechT5Processor.from_pretrained(
                        model_name)
                    self.loaded_models[model_key] = SpeechT5ForTextToSpeech.from_pretrained(
                        model_name)

            if service == "speecht5":
                self.loaded_processors[model_key] = SpeechT5Processor.from_pretrained(
                    model_name)
                self.loaded_models[model_key] = SpeechT5ForTextToSpeech.from_pretrained(
                    model_name)

                # Load vocoder if not already loaded
                if "vocoder" not in self.loaded_models:
                    self.loaded_models["vocoder"] = SpeechT5HifiGan.from_pretrained(
                        "microsoft/speecht5_hifigan")

                # Load speaker embeddings if not already loaded
                if self.speaker_embeddings is None:
                    # Create random speaker embeddings for different voices
                    self.speaker_embeddings = {
                        "male": torch.randn(1, 512) * 0.5,
                        "female": torch.randn(1, 512) * 0.5,
                        "announcer": torch.randn(1, 512) * 0.5
                    }

            print(f"Loaded {service} model for {voice_type}")

        return self.loaded_models[model_key], self.loaded_processors[model_key]

    def get_voice_for_gender(self, gender: str, speaker: str = None) -> Tuple[str, str]:
        """
        Get an appropriate voice for the given gender and speaker
        Returns a tuple of (service, voice_type)
        """
        # Rotate through services for variety
        service = self.tts_services[self.current_service_index]
        self.current_service_index = (
            self.current_service_index + 1) % len(self.tts_services)

        # Special case for announcer
        if speaker and speaker.lower() == "announcer":
            return service, "announcer"

        return service, gender

    def generate_audio_part(self, text: str, service: str, voice_type: str) -> str:
        """Generate audio for a single part using the specified service"""
        if service == "mms":
            return self._generate_mms_audio(text, voice_type)
        elif service == "speecht5":
            return self._generate_speecht5_audio(text, voice_type)
        else:
            raise ValueError(f"Unknown service: {service}")

    def _generate_mms_audio(self, text: str, voice_type: str) -> str:
        """Generate audio using MMS model from Hugging Face"""
        model, processor = self._load_model("mms", voice_type)

        # Get speaker ID
        speaker_id = self.mms_speakers[voice_type]
        inputs = processor(text=text, return_tensors="pt")

        # Add speaker embedding
        speaker_embeddings = torch.tensor(
            [[1.0 if x == speaker_id else 0.0 for x in range(len(self.mms_speakers))]])
        inputs["speaker_embeddings"] = speaker_embeddings

        # Generate audio
        with torch.no_grad():
            output = model.generate_speech(**inputs)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            sf.write(temp_file.name, output.numpy(),
                     model.config.sampling_rate, format="mp3")
            return temp_file.name

    def _generate_speecht5_audio(self, text: str, voice_type: str) -> str:
        """Generate audio using SpeechT5 model from Microsoft"""
        model, processor = self._load_model("speecht5", voice_type)
        vocoder = self.loaded_models["vocoder"]

        speaker_embedding = self.speaker_embeddings[voice_type]
        inputs = processor(text=text, return_tensors="pt")
        speech = model.generate_speech(
            inputs["input_ids"],
            speaker_embeddings=speaker_embedding,
            vocoder=vocoder
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            sf.write(temp_file.name, speech.numpy(), 16000, format="mp3")
            return temp_file.name

    def combine_audio_files(self, audio_files: List[str], output_file: str):
        """Combine multiple audio files using ffmpeg"""
        file_list = None
        try:
            # Create file list for ffmpeg
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
                file_list = f.name

            # Combine audio files
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    file_list,
                    "-c",
                    "copy",
                    output_file,
                ],
                check=True,
            )

            return True
        except Exception as e:
            print(f"Error combining audio files: {str(e)}")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return False
        finally:
            # Clean up temporary files
            if file_list and os.path.exists(file_list):
                os.unlink(file_list)
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    try:
                        os.unlink(audio_file)
                    except Exception as e:
                        print(f"Error cleaning up {audio_file}: {str(e)}")

    def generate_silence(self, duration_ms: int) -> str:
        """Generate a silent audio file of specified duration"""
        output_file = os.path.join(
            self.audio_dir, f"silence_{duration_ms}ms.mp3")
        if not os.path.exists(output_file):
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "lavfi",
                    "-i",
                    f"anullsrc=r=24000:cl=mono:d={duration_ms/1000}",
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "48k",
                    output_file,
                ]
            )
        return output_file

    def generate_audio(self, question: Dict) -> str:
        """
        Generate audio for the entire question.
        Returns the path to the generated audio file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.audio_dir, f"question_{timestamp}.mp3")

        try:
            # Parse conversation into parts
            parts = self.parse_conversation(question)

            audio_parts = []
            current_section = None

            # Generate silence files for pauses
            long_pause = self.generate_silence(2000)  # 2 second pause
            short_pause = self.generate_silence(500)  # 0.5 second pause

            for speaker, text, gender in parts:
                # Detect section changes and add appropriate pauses
                if speaker.lower() == "announcer":
                    # Introduction
                    if any(word in text.lower() for word in ["sikiliza", "mazungumzo", "kisha"]):
                        if current_section is not None:
                            audio_parts.append(long_pause)
                        current_section = "intro"
                    # Question or options
                    elif any(word in text.lower() for word in ["swali", "maswali", "chagua"]):
                        audio_parts.append(long_pause)
                        current_section = "question"
                elif current_section == "intro":
                    audio_parts.append(long_pause)
                    current_section = "conversation"
                # Get appropriate voice for this speaker
                service, voice_type = self.get_voice_for_gender(
                    gender, speaker)
                print(
                    f"Using {service} voice {voice_type} for {speaker} ({gender})")

                # Generate audio for this part
                audio_file = self.generate_audio_part(
                    text, service, voice_type)
                if not audio_file:
                    raise Exception("Failed to generate audio part")
                audio_parts.append(audio_file)

                # Add short pause between conversation turns
                if current_section == "conversation":
                    audio_parts.append(short_pause)
            if not self.combine_audio_files(audio_parts, output_file):
                raise Exception("Failed to combine audio files")

            return output_file

        except Exception as e:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise Exception(f"Audio generation failed: {str(e)}")
