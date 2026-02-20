import os
import pandas as pd
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

CHROMA_DIR = "./chroma_db"


def load_exercise_docs():
    df = pd.read_csv("data/megaGymDataset.csv")
    df = df.drop(columns=["Unnamed: 0"])
    df = df.dropna(subset=["Title", "Desc"])

    docs = []
    for _, row in df.iterrows():
        content = (
            f"{row['Title']} targets {row.get('BodyPart', 'N/A')}, "
            f"type: {row.get('Type', 'N/A')}, "
            f"equipment: {row.get('Equipment', 'N/A')}, "
            f"level: {row.get('Level', 'N/A')}. "
            f"Description: {row['Desc']}"
        )
        metadata = {
            "title": str(row.get("Title", "")),
            "body_part": str(row.get("BodyPart", "")),
            "equipment": str(row.get("Equipment", "")),
            "level": str(row.get("Level", "")),
            "type": str(row.get("Type", "")),
            "source": "exercises",
        }
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def load_nutrient_docs():
    df = pd.read_csv("data/nutrition.csv")
    df = df.drop(columns=["Unnamed: 0"])
    df = df.dropna(subset=["name"])

    docs = []
    for _, row in df.iterrows():
        content = (
            f"{row['name']}: "
            f"{row.get('calories', 'N/A')} calories, "
            f"{row.get('protein', 'N/A')}g protein, "
            f"{row.get('fat', 'N/A')}g fat, "
            f"{row.get('carbohydrate', 'N/A')}g carbs, "
            f"{row.get('fiber', 'N/A')}g fiber "
            f"per {row.get('serving_size', 'N/A')}."
        )
        metadata = {
            "name": str(row.get("name", "")),
            "calories": str(row.get("calories", "")),
            "protein": str(row.get("protein", "")),
            "fat": str(row.get("fat", "")),
            "carbohydrate": str(row.get("carbohydrate", "")),
            "source": "nutrients",
        }
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def ingest():
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    exercise_docs = load_exercise_docs()
    nutrient_docs = load_nutrient_docs()

    print(f"Loaded {len(exercise_docs)} exercise documents.")
    print(f"Loaded {len(nutrient_docs)} nutrient documents.")

    print("Ingesting exercises into ChromaDB...")
    Chroma.from_documents(
        documents=exercise_docs,
        embedding=embeddings,
        collection_name="exercises",
        persist_directory=CHROMA_DIR,
    )

    print("Ingesting nutrients into ChromaDB...")
    Chroma.from_documents(
        documents=nutrient_docs,
        embedding=embeddings,
        collection_name="nutrients",
        persist_directory=CHROMA_DIR,
    )

    print(
        f"Ingested {len(exercise_docs)} exercises and "
        f"{len(nutrient_docs)} nutrients into ChromaDB."
    )


if __name__ == "__main__":
    ingest()