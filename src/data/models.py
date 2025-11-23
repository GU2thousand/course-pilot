from pydantic import BaseModel, Field
from typing import List, Optional

class Course(BaseModel):
    """
    Represents a single course offering.
    """
    course_id: str = Field(..., description="Unique identifier, e.g., 'CS-GY 6003'")
    name: str = Field(..., description="Course title, e.g., 'Intro to AI'")
    instructor: str = Field(..., description="Name of the instructor")
    school: str = Field(..., description="School offering the course")
    term: str = Field(..., description="Term, e.g., 'Spring 2026'")
    
    description: Optional[str] = Field(None, description="Course description")
    schedule: Optional[str] = Field(None, description="Meeting times and location")
    units: Optional[str] = Field(None, description="Number of credits")
    instruction_mode: Optional[str] = Field(None, description="e.g., In-Person, Online")
    
    # Rate My Professor Data (to be populated later)
    rmp_rating: Optional[float] = Field(None, description="Average rating from RMP (0-5)")
    rmp_num_ratings: Optional[int] = Field(None, description="Number of ratings on RMP")
    rmp_summary: Optional[str] = Field(None, description="AI-generated summary of student reviews")
    
    def to_document_text(self) -> str:
        """
        Converts the course info into a text format suitable for embedding.
        """
        text = f"Course: {self.course_id} - {self.name}\n"
        text += f"Instructor: {self.instructor}\n"
        text += f"School: {self.school}\n"
        if self.description:
            text += f"Description: {self.description}\n"
        if self.rmp_summary:
            text += f"Professor Reviews: {self.rmp_summary}\n"
        return text
