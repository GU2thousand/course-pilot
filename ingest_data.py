import asyncio
import os
from src.data.fetcher import JSONFileFetcher
from src.data.rmp import RMPSearcher, RMPAggregator
from src.data.processor import DocumentProcessor
from src.vector_store.store import CourseVectorStore
from dotenv import load_dotenv

load_dotenv()

def ingest_data():
    print("🚀 Starting Data Ingestion...")
    
    # 1. Fetch Courses (Mock Data for now)
    print("📦 Loading courses from JSON...")
    fetcher = JSONFileFetcher("src/data/courses.json")
    courses = fetcher.fetch_courses()
    print(f"✅ Loaded {len(courses)} courses.")
    
    # 2. Enrich with RMP Data
    print("🔍 Enriching with Rate My Professor data (this may take a moment)...")
    searcher = RMPSearcher()
    aggregator = RMPAggregator()
    
    for course in courses:
        if course.instructor and course.instructor != "Staff":
            print(f"   Processing {course.instructor}...")
            # Search
            content = searcher.search_professor(course.instructor, "NYU")
            # Summarize
            rmp_data = aggregator.summarize_reviews(course.instructor, content)
            
            # Update Course Object
            course.rmp_rating = rmp_data.get("rating", 0.0)
            course.rmp_summary = rmp_data.get("summary", "")
            course.rmp_num_ratings = 0 # Not extracted currently
            
    print("✅ Enrichment complete.")
    
    # 3. Process for Vector Store
    print("⚙️ Processing documents...")
    documents, metadatas, ids = DocumentProcessor.process_courses(courses)
    
    # 4. Store in ChromaDB
    print("💾 Storing in ChromaDB...")
    vector_store = CourseVectorStore()
    vector_store.add_courses(documents, metadatas, ids)
    
    print("🎉 Data Ingestion Finished Successfully!")

if __name__ == "__main__":
    ingest_data()
