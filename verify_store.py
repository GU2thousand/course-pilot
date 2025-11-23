from src.vector_store.store import CourseVectorStore
from dotenv import load_dotenv

load_dotenv()

def verify():
    print("🕵️ Verifying Vector Store...")
    store = CourseVectorStore()
    
    query = "I want to learn about Artificial Intelligence and Neural Networks"
    print(f"Query: '{query}'")
    
    results = store.search_courses(query, n_results=3)
    
    print(f"\nFound {len(results)} results:")
    for res in results:
        meta = res['metadata']
        print(f"- {meta['course_id']}: {meta['name']} (Instructor: {meta['instructor']})")
        print(f"  Distance: {res['distance']}")

if __name__ == "__main__":
    verify()
