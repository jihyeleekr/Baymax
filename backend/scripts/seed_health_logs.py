import os
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables (.env)
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_NAME = os.getenv("MONGODB_NAME", "baymax")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set in .env")

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_NAME]

# Path to seed JSON file
seed_file = BASE_DIR / "data" / "health_logs_seed.json"


def main():
    print(f"📂 Loading seed data from: {seed_file}")

    if not seed_file.exists():
        raise FileNotFoundError(f"Seed file does not exist: {seed_file}")

    # Load JSON sample data
    with open(seed_file, "r", encoding="utf-8") as f:
        docs = json.load(f)

    # Add created_at timestamp to each document
    for doc in docs:
        doc["created_at"] = datetime.utcnow()

    # Insert documents into MongoDB collection
    result = db.health_logs.insert_many(docs)

    print(f"Inserted {len(result.inserted_ids)} documents into 'health_logs'.")
    print("   Inserted IDs:")
    print([str(_id) for _id in result.inserted_ids])


if __name__ == "__main__":
    main()
