from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

CHROMA_DIR = "./chroma_db"


def get_collection(collection_name):
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )


def query_exercises(query, k=3):
    store = get_collection("exercises")
    results = store.similarity_search(query, k=k)
    return [doc.page_content for doc in results]


def query_nutrients(query, k=3):
    store = get_collection("nutrients")
    results = store.similarity_search(query, k=k)
    return [doc.page_content for doc in results]