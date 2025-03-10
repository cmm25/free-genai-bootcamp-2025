import chromadb
from chromadb.utils import embedding_functions
import json
import os
from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer

class SwahiliEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_name='sentence-transformers/distiluse-base-multilingual-cased-v2'):
        self.model = SentenceTransformer(model_name)
        
    def __call__(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return [[0.0] * 512 for _ in range(len(texts))]

class QuestionVectorStore:
    def __init__(self, persist_directory: str = './data/vectorstore'):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = SwahiliEmbeddingFunction()
        
        self.collections = {
            "section2": self.client.get_or_create_collection(
                name="section2_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "Swahili questions - Section 2"}
            ),
            "section3": self.client.get_or_create_collection(
                name="section3_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "Swahili phrase matching questions - Section 3"}
            )
        }
    
    def add_questions(self, section_num: int, questions: List[Dict], content_id: str):
        if section_num not in [2, 3]:
            raise ValueError("Only sections 2 and 3 are currently supported")
        
        collection = self.collections[f"section{section_num}"]
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, question in enumerate(questions):
            question_id = f"{content_id}_{section_num}_{idx}"
            ids.append(question_id)
            
            # Store full question structure as metadata.
            metadatas.append({
                "content_id": content_id,
                "section": section_num,
                "question_index": idx,
                "full_structure": json.dumps(question)
            })
            
            # Searchable document from content
            if section_num == 2:
                document = f"""
                Situation: {question['Introduction']}
                Dialogue: {question['Conversation']}
                Question: {question['Question']}
                """
            else: 
                document = f"""
                Situation: {question['Situation']}
                Question: {question['Question']}
                """
            documents.append(document)
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    def search_similar_questions(self, section_num: int, query: str, n_results: int = 5) -> List[Dict]:
        if section_num not in [2, 3]:
            raise ValueError("Only sections 2 and 3 are currently supported")
        
        collection = self.collections[f"section{section_num}"]
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        questions = []
        # results formatting
        for idx, metadata in enumerate(results['metadatas'][0]):
            question_data = json.loads(metadata['full_structure'])
            question_data['similarity_score'] = results['distances'][0][idx]
            questions.append(question_data)
        
        return questions
    
    def get_question_by_id(self, section_num: int, question_id: str) -> Optional[Dict]:
        if section_num not in [2, 3]:
            raise ValueError("Only sections 2 and 3 are currently supported")
            
        collection = self.collections[f"section{section_num}"]
        
        result = collection.get(
            ids=[question_id],
            include=['metadatas']
        )
        
        if result['metadatas']:
            return json.loads(result['metadatas'][0]['full_structure'])
        return None
    
    def parse_questions_from_file(self, filename: str) -> List[Dict]:
        """Parse questions from a structured text file"""
        questions = []
        current_question = {}
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()                
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('<question>'):
                    current_question = {}
                elif line.startswith('Introduction:'):
                    i += 1
                    if i < len(lines):
                        current_question['Introduction'] = lines[i].strip()
                elif line.startswith('Conversation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Conversation'] = lines[i].strip()
                elif line.startswith('Situation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Situation'] = lines[i].strip()
                elif line.startswith('Question:'):
                    i += 1
                    if i < len(lines):
                        current_question['Question'] = lines[i].strip()
                elif line.startswith('Options:'):
                    options = []
                    for _ in range(4):
                        i += 1
                        if i < len(lines):
                            option = lines[i].strip()
                            if option.startswith('1.') or option.startswith('2.') or option.startswith('3.') or option.startswith('4.'):
                                options.append(option[2:].strip())
                    current_question['Options'] = options
                elif line.startswith('</question>'):
                    if current_question:
                        questions.append(current_question)
                        current_question = {}
                i += 1
            return questions
        except Exception as e:
            print(f"Error parsing questions from {filename}: {str(e)}")
            return []
    
    def index_questions_file(self, filename: str, section_num: int):
        # Extract content ID from filename
        content_id = os.path.basename(filename).split('_section')[0]
        # Parse questions from file
        questions = self.parse_questions_from_file(filename)
        
        # Add to vector store
        if questions:
            self.add_questions(section_num, questions, content_id)
            print(f"Indexed {len(questions)} questions from {filename}")

if __name__ == "__main__":
    store = QuestionVectorStore()
    
    question_files = [
        ("./data/questions/swahili_content1_section2.txt", 2)
    ]
    
    for filename, section_num in question_files:
        if os.path.exists(filename):
            store.index_questions_file(filename, section_num)

    similar = store.search_similar_questions(2, "Swali kuhusu sikukuu za kitamaduni", n_results=1)