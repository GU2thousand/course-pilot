from src.data.rmp import RMPSearcher, RMPAggregator
import os

def test_rmp():
    print("Testing RMP Integration...")
    
    # Check keys
    if not os.getenv("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY not found.")
        return
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found.")
        return

    searcher = RMPSearcher()
    aggregator = RMPAggregator()
    
    prof_name = "Yann LeCun"
    school = "NYU"
    
    print(f"Searching for {prof_name} at {school}...")
    content = searcher.search_professor(prof_name, school)
    
    if content:
        print(f"Found content (length {len(content)}). Generating summary...")
        result = aggregator.summarize_reviews(prof_name, content)
        print("\nResult:")
        print(f"Rating: {result['rating']}")
        print(f"Summary: {result['summary']}")
    else:
        print("No content found.")

if __name__ == "__main__":
    test_rmp()
