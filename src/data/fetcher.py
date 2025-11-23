from abc import ABC, abstractmethod
from typing import List
from bs4 import BeautifulSoup
import logging
from .models import Course

logger = logging.getLogger(__name__)

import json
from typing import List
from .models import Course
import logging

logger = logging.getLogger(__name__)

class CourseFetcher(ABC):
    @abstractmethod
    def fetch_courses(self) -> List[Course]:
        pass

class JSONFileFetcher(CourseFetcher):
    """
    Parses courses from a JSON file.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def fetch_courses(self) -> List[Course]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Course(**item) for item in data]
        except Exception as e:
            logger.error(f"Error reading file {self.file_path}: {e}")
            return []


class MockCourseFetcher(CourseFetcher):
    """
    Returns dummy data for testing.
    """
    def fetch_courses(self) -> List[Course]:
        return [
            Course(
                course_id="CS-GY 6003",
                name="Foundations of Artificial Intelligence",
                instructor="Yann LeCun",
                school="Tandon School of Engineering",
                term="Spring 2026",
                description="Introduction to AI agents, search, and learning.",
                schedule="Mon 2:00PM - 4:30PM"
            ),
            Course(
                course_id="CS-GY 9999",
                name="Deep Learning",
                instructor="Andrew Ng",
                school="Tandon School of Engineering",
                term="Spring 2026",
                description="Neural networks and backpropagation.",
                schedule="Wed 6:00PM - 8:30PM"
            )
        ]
