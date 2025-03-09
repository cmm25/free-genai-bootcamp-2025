import os
import sys
import json
from audiogeneration import AudioGenerator


def test_single_phrase():
    """Test generating audio for a single Swahili phrase"""
    generator = AudioGenerator()
    phrases = [
        "Habari ya leo?",  
        "Jina langu ni Zawadi.",  
        "Karibu Tanzania."  
    ]

    for i, phrase in enumerate(phrases):
        print(f"Generating audio for phrase {i+1}: {phrase}")

        # Create a simple question structure
        question = {
            "Introduction": "Maswali ya Swahili",
            "Conversation": phrase,
            "Question": "Ulisikia nini?",
            "Options": [
                "Chaguo la kwanza",
                "Chaguo la pili",
                "Chaguo la tatu",
                "Chaguo la nne"
            ]
        }

        try:
            output_file = generator.generate_audio(question)
            print(f"Audio generated successfully: {output_file}")
        except Exception as e:
            print(f"Error generating audio: {str(e)}")


def test_conversation():
    """Test generating audio for a Swahili conversation"""
    generator = AudioGenerator()

    conversation = """
                        Zawadi: Hujambo rafiki yangu! Umeamkaje?
                        Baraka: Sijambo sana. Nimeamka salama.
                        Zawadi: Unaenda wapi sasa?
                        Baraka: Ninaenda sokoni. Ninahitaji kununua matunda na mboga.
                        Zawadi: Nitakwenda pamoja nawe. Je, unatumia dakika ngapi kwenda sokoni?
                        Baraka: Dakika kumi na tano kwa kutembea, dakika tano kwa pikipiki.
                        Zawadi: Basi twende kwa pikipiki, tuna haraka leo.
                """

    
    question = {
        "Introduction": "Sikiliza mazungumzo yafuatayo kisha ujibu maswali.",
        "Conversation": conversation,
        "Question": "Watu wawili wanaenda wapi?",
        "Options": [
            "Sokoni",
            "Shuleni",
            "Kanisani",
            "Ofisini"
        ]
    }

    try:
        output_file = generator.generate_audio(question)
        print(f"Conversation audio generated successfully: {output_file}")
    except Exception as e:
        print(f"Error generating conversation audio: {str(e)}")


def test_time_phrases():
    """Test generating audio for time expressions in Swahili"""
    generator = AudioGenerator()

    time_phrases = [
        "dakika tano.",
        "dakika kumi.",
        "dakika kumi na tano."
    ]

    for i, phrase in enumerate(time_phrases):
        print(f"Generating audio for time phrase {i+1}: {phrase}")

        question = {
            "Introduction": "Sikiliza muda huu",
            "Conversation": f"Muda ni {phrase}",
            "Question": "Muda gani ulisikia?",
            "Options": [
                "Dakika tano",
                "Dakika kumi",
                "Dakika kumi na tano",
                "Saa moja"
            ]
        }

        try:
            output_file = generator.generate_audio(question)
            print(f"Time phrase audio generated successfully: {output_file}")
        except Exception as e:
            print(f"Error generating time phrase audio: {str(e)}")


def main():
    """Run audio generation tests"""
    print("=== Testing Audio Generation for Swahili ===")

    os.makedirs("test_output", exist_ok=True)

    print("\n1. Testing single phrases...")
    test_single_phrase()

    print("\n2. Testing conversation...")
    test_conversation()

    print("\n3. Testing time phrases...")
    test_time_phrases()

    print("\nAll tests completed!")


if __name__ == "__main__":
    main()

