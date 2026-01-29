"""
Build ChromaDB vector database from exercise dataset

Run this once before starting the API:
    cd backend
    python build_database.py
"""

import sys
from pathlib import Path
from app.services.rag_service import rag_service

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))


def main():
    """Build the vector database"""
    # Get paths
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent

    # Try to find the CSV file
    csv_paths = [
        project_root / "data" / "raw" / "megaGymDataset.csv",
        project_root / "data" / "raw" / "sample_exercises.csv",
    ]

    csv_path = None
    for path in csv_paths:
        if path.exists():
            csv_path = path
            break

    if not csv_path:
        print("\nError: No exercise dataset found!")
        print("\nPlease either:")
        print("1. Download megaGymDataset.csv from Kaggle")
        print("   URL: https://www.kaggle.com/datasets/niharika41298/gym-exercise-data")
        print("   Place in: data/raw/megaGymDataset.csv")
        print("\n2. Or use the sample dataset that was created")
        print("   Location: data/raw/sample_exercises.csv")
        return

    print(f"\nUsing dataset: {csv_path.name}")

    try:
        # Build vectorstore
        rag_service.build_vectorstore(str(csv_path))

        print(f"\n{'='*60}")
        print("Database Built Successfully!")
        print(f"{'='*60}")

        # Test search
        print("\nTesting search functionality...")
        results = rag_service.search_exercises("chest exercises for beginners", k=3)

        print(f"\nFound {len(results)} exercises:")
        for i, doc in enumerate(results, 1):
            print(
                f"{i}. {doc.metadata['title']} ({doc.metadata['level']}, {doc.metadata['body_part']})"
            )

        print(f"\n{'='*60}")
        print("All Systems Ready!")
        print(f"{'='*60}")
        print("\nNext step: Start the API server")
        print("  python -m app.main")

    except Exception as e:
        print(f"\nError building database: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
