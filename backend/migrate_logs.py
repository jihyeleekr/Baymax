from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["baymax"]

# 1) See what user_ids exist and how many docs are missing user_id
print("Distinct user_ids:", db.health_logs.distinct("user_id"))
print("Count with no user_id:", db.health_logs.count_documents({"user_id": {"$exists": False}}))

# 2) OPTIONAL: set missing user_id to 'anonymous'
result = db.health_logs.update_many(
    {"user_id": {"$exists": False}},
    {"$set": {"user_id": "anonymous"}}
)
print(f"Updated {result.modified_count} logs to user_id='anonymous'")

client.close()

