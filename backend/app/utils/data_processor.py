"""
Exercise data processor
Prepares exercise data for RAG system
"""

import pandas as pd
import re
from typing import List, Dict
from pathlib import Path


class ExerciseDataProcessor:
    """
    Process exercise dataset for vector storage

    Takes raw CSV and creates searchable documents
    """

    def __init__(self, csv_path: str):
        """
        Initialize with path to CSV file

        Args:
            csv_path: Path to exercise CSV file
        """
        self.csv_path = Path(csv_path)

        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset not found: {csv_path}")

        self.df = pd.read_csv(csv_path)
        self.processed_docs = []

        print(f"Loaded {len(self.df)} exercises from {csv_path}")

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if pd.isna(text):
            return ""

        # Convert to string
        text = str(text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,!?-]", "", text)

        return text.strip()

    def create_document_text(self, row: pd.Series) -> str:
        """
        Create searchable document from exercise row

        Combines all exercise attributes into a single searchable text

        Args:
            row: DataFrame row with exercise data

        Returns:
            Formatted document string
        """
        parts = [
            f"Exercise: {row['Title']}",
            f"Description: {self.clean_text(row['Desc'])}",
            f"Type: {row['Type']}",
            f"Body Part: {row['BodyPart']}",
            f"Equipment: {row['Equipment']}",
            f"Level: {row['Level']}",
        ]

        return " | ".join(parts)

    def process(self) -> List[Dict[str, any]]:
        """
        Process all exercises into documents

        Returns:
            List of document dictionaries with text and metadata
        """
        # Remove rows with missing critical data
        self.df = self.df.dropna(subset=["Title", "Desc"])

        print(f"Processing {len(self.df)} valid exercises...")

        for idx, row in self.df.iterrows():
            doc = {
                "id": f"exercise_{idx}",
                "text": self.create_document_text(row),
                "metadata": {
                    "title": row["Title"],
                    "type": row["Type"],
                    "body_part": row["BodyPart"],
                    "equipment": row["Equipment"],
                    "level": row["Level"],
                    "description": self.clean_text(row["Desc"])[
                        :200
                    ],  # First 200 chars
                },
            }
            self.processed_docs.append(doc)

        print(f"✓ Processed {len(self.processed_docs)} exercises")
        return self.processed_docs


# Test function
if __name__ == "__main__":
    # Test with sample data
    processor = ExerciseDataProcessor("../../data/raw/sample_exercises.csv")
    docs = processor.process()

    print(f"\nSample document:")
    print(docs[0]["text"][:200])
    print(f"\nMetadata: {docs[0]['metadata']}")
