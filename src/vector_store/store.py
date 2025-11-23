import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class CourseVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Google Generative AI Embeddings
        # We use the direct google.generativeai embedding function provided by Chroma or a custom one if needed.
        # For simplicity and to match our successful direct API usage, let's use the default google ef if available,
        # or build a simple wrapper around genai.embed_content.
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=google_api_key,
            model_name="models/text-embedding-004"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="courses",
            embedding_function=self.embedding_fn
        )

    def add_courses(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """
        Adds course documents to the vector store.
        """
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Added {len(documents)} courses to ChromaDB.")

    def search_courses(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for relevant courses based on a query.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Chroma returns a dict of lists. We want to flatten it to a list of dicts for easier use.
        # results['metadatas'][0] contains the metadata for the first query (we only have one).
        if not results['metadatas']:
            return []
            
        flattened_results = []
        for i, metadata in enumerate(results['metadatas'][0]):
            flattened_results.append({
                "metadata": metadata,
                "document": results['documents'][0][i],
                "distance": results['distances'][0][i] if results['distances'] else None
            })
            
        return flattened_results
