from typing import Dict, List, Optional
import requests
from sentence_transformers import SentenceTransformer
import json
import numpy as np
from .vectorstore import QuestionVectorStore
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
class SwahiliQuestionGenerator:
    def __init__(self):
        self.model_name = "Jacaranda/UlizaLlama"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.vector_store = QuestionVectorStore()
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def _invoke_model(self, prompt: str) -> Optional[str]:
        """Generate text using the language model."""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.95,
                do_sample=True
            )
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text.replace(prompt, "").strip()
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            return None
    def generate_similar_question(self, section_num: int, topic: str) -> Dict:
        """Generate a new question similar to existing ones on a given Swahili topic"""
        similar_questions = self.vector_store.search_similar_questions(section_num, topic, n_results=3)
        
        if not similar_questions:
            return None
        
        context = "Here are some example Swahili listening comprehension questions:\n\n"
        for idx, q in enumerate(similar_questions, 1):
            if section_num == 2:
                context += f"Example {idx}:\n"
                context += f"Introduction: {q.get('Introduction', '')}\n"
                context += f"Conversation: {q.get('Conversation', '')}\n"
                context += f"Question: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Options:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            else:  
                context += f"Example {idx}:\n"
                context += f"Situation: {q.get('Situation', '')}\n"
                context += f"Question: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Options:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            context += "\n"

        
        prompt = f"""Based on the following example Swahili listening comprehension questions, create a new question about {topic}.
        The question should follow the same format but be different from the examples.
        Make sure the question tests listening comprehension and has a clear correct answer.
        Make sure all text is in Swahili except for instructional text.
        
        {context}
        
        Generate a new question following the exact same format as above. Include all components (Introduction/Situation, 
        Conversation/Question, and Options). Make sure the question is challenging but fair, and the options are plausible 
        but with only one clearly correct answer. Return ONLY the question without any additional text.
        
        New Question:
        """

        # Generate new question
        response = self._invoke_model(prompt)
        if not response:
            return None
        try:
            lines = response.strip().split('\n')
            question = {}
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("Introduction:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Introduction'
                    current_value = [line.replace("Introduction:", "").strip()]
                elif line.startswith("Conversation:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Conversation'
                    current_value = [line.replace("Conversation:", "").strip()]
                elif line.startswith("Situation:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Situation'
                    current_value = [line.replace("Situation:", "").strip()]
                elif line.startswith("Question:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Question'
                    current_value = [line.replace("Question:", "").strip()]
                elif line.startswith("Options:"):
                    if current_key:
                        question[current_key] = ' '.join(current_value)
                    current_key = 'Options'
                    current_value = []
                elif line[0].isdigit() and line[1] == "." and current_key == 'Options':
                    current_value.append(line[2:].strip())
                elif current_key:
                    current_value.append(line)
            
            if current_key:
                if current_key == 'Options':
                    question[current_key] = current_value
                else:
                    question[current_key] = ' '.join(current_value)
            
            
            if 'Options' not in question or len(question.get('Options', [])) != 4:
                
                question['Options'] = [
                    "Kula sima",
                    "Kula mahamri",
                    "Kula saladi",
                    "Kunywa maziwa"
                ]
            
            return question
        except Exception as e:
            print(f"Error parsing generated question: {str(e)}")
            return None

    def get_feedback(self, question: Dict, selected_answer: int) -> Dict:
        """Generate feedback for the selected answer"""
        if not question or 'Options' not in question:
            return None

        prompt = f"""Given this Swahili listening comprehension question and the selected answer, provide feedback explaining if it's correct 
        and why. Keep the explanation clear and concise.
        
        """
        if 'Introduction' in question:
            prompt += f"Introduction: {question['Introduction']}\n"
            prompt += f"Conversation: {question['Conversation']}\n"
        else:
            prompt += f"Situation: {question['Situation']}\n"
        
        prompt += f"Question: {question['Question']}\n"
        prompt += "Options:\n"
        for i, opt in enumerate(question['Options'], 1):
            prompt += f"{i}. {opt}\n"
        
        prompt += f"\nSelected Answer: {selected_answer}\n"
        prompt += "\nProvide feedback in JSON format with these fields:\n"
        prompt += "- correct: true/false\n"
        prompt += "- explanation: brief explanation of why the answer is correct/incorrect in both English and Swahili\n"
        prompt += "- correct_answer: the number of the correct option (1-4)\n"

        # Get feedback
        response = self._invoke_model(prompt)
        if not response:
            return None

        try:
            response_text = response.strip()
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_content = response_text.split("```")[1].strip()
            else:
                json_content = response_text
                
            feedback = json.loads(json_content)
            return feedback
        except:
            return {
                "correct": False,
                "explanation": {
                    "English": "Unable to generate detailed feedback. Please try again.",
                    "Swahili": "Kushindwa kutoa maoni ya kina. Tafadhali jaribu tena."
                },
                "correct_answer": 1  # Default to first option
            }