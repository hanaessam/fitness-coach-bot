import pandas as pd
import re
from typing import List, Dict
from pathlib import Path

class ExerciseDataProcessor:
    """Preprocess exercise data for RAG system"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset not found: {csv_path}")
        
        self.df = pd.read_csv(csv_path)
        self.processed_docs = []
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if pd.isna(text):
            return ""
        text = re.sub(r'\s+', ' ', str(text))
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()
    
    def create_document_text(self, row: pd.Series) -> str:
        """Create searchable document from exercise row"""
        parts = [
            f"Exercise: {row['Title']}",
            f"Description: {self.clean_text(row['Desc'])}",
            f"Type: {row['Type']}",
            f"Body Part: {row['BodyPart']}",
            f"Equipment: {row['Equipment']}",
            f"Level: {row['Level']}"
        ]
        return " | ".join(parts)
    
    def process(self) -> List[Dict[str, any]]:
        """Process all exercises into documents"""
        self.df = self.df.dropna(subset=['Title', 'Desc'])
        
        for idx, row in self.df.iterrows():
            doc = {
                'id': f"exercise_{idx}",
                'text': self.create_document_text(row),
                'metadata': {
                    'title': row['Title'],
                    'type': row['Type'],
                    'body_part': row['BodyPart'],
                    'equipment': row['Equipment'],
                    'level': row['Level']
                }
            }
            self.processed_docs.append(doc)
        
        print(f"Processed {len(self.processed_docs)} exercises")
        return self.processed_docs