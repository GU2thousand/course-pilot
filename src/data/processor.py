from typing import List, Tuple, Dict, Any
from src.data.models import Course

class DocumentProcessor:
    @staticmethod
    def process_courses(courses: List[Course]) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Converts a list of Course objects into lists of documents, metadatas, and ids suitable for ChromaDB.
        """
        documents = []
        metadatas = []
        ids = []

        for course in courses:
            # Construct a rich text representation for embedding
            # We include all key fields so the semantic search can match on any aspect.
            doc_text = f"""
            Course Code: {course.course_id}
            Course Name: {course.name}
            Instructor: {course.instructor}
            School: {course.school}
            Term: {course.term}
            Description: {course.description}
            Schedule: {course.schedule}
            Instruction Mode: {course.instruction_mode}
            
            Professor Rating: {course.rmp_rating if course.rmp_rating else 'N/A'}
            Professor Summary: {course.rmp_summary if course.rmp_summary else 'N/A'}
            """
            
            # Clean up whitespace
            doc_text = "\n".join([line.strip() for line in doc_text.split('\n') if line.strip()])
            
            documents.append(doc_text)
            
            # Metadata for filtering and retrieval
            metadatas.append({
                "course_id": course.course_id,
                "name": course.name,
                "instructor": course.instructor,
                "school": course.school,
                "units": course.units,
                "rating": course.rmp_rating if course.rmp_rating else 0.0,
                "rmp_summary": course.rmp_summary if course.rmp_summary else "N/A"
            })
            
            ids.append(course.course_id)

        return documents, metadatas, ids
