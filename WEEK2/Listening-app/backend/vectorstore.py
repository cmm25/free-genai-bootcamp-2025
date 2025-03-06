import chromadb
from chromadb.utils import embedding_functions
import json
import os
from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer

class SwahiliEmbeddingFunction(embedding_functions.DefaultEmbeddingFunction):
    def __init__(self,model_name ='sentence-transformers/distiluse-base-multilingual-cased-v2'):
        self.model = SentenceTransformer(model_name)
        
    def __call__(self, texts:List[str])->List[List[float]]:
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return [[0.0] * 512 for _ in range(len(texts))]

class QuestionVectorStore:
    def __init__( self,persist_directory:str ='backend/data/vectorstore'):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embeddingFunction = SwahiliEmbeddingFunction()
        
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
        
        def add_questions(self, section_num: int, questions: List[Dict], video_id: str):
            if section_num not in [2, 3]:
                raise ValueError("Only sections 2 and 3 are currently supported")
            
            collection = self.collections[f"section{section_num}"]
            
            ids = []
            documents = []
            metadatas = []
            
            for idx, question in enumerate(questions):
                question_id = f"{video_id}_{section_num}_{idx}"
                ids.append(question_id)
                
                # Store full question structure as metadata.
                metadatas.append({
                    "video_id": video_id,
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
                ids = ids,
                documents = documents,
                metadatas = metadatas
            )
        def search_similar_questions(self,section_num: int,query: str,n_results: int = 5) -> List[Dict]:
            if section_num not in [2,3]:
                raise ValueError ("Only sections 2 and 3 are currently supported")
            
            collection = self.collections[f"section{section_num}"]
            
            results = collection.query(
                query_texts = [query],
                n_results = n_results
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