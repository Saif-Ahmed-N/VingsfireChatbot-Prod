import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGO_URI = os.getenv("MONGO_CONNECTION_STRING")
DATABASE_NAME = "vingsfire_leads"
COLLECTION_NAME = "proposals"

client = None
collection = None

try:
    if not MONGO_URI:
        raise ConfigurationError("MONGO_CONNECTION_STRING is not set in the .env file.")
    ca = certifi.where()
    client = MongoClient(MONGO_URI, tlsCAFile=ca)
    client.admin.command('ping')
    print("MongoDB connection successful.")
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
except (ConnectionFailure, ConfigurationError) as e:
    print(f"FATAL: Could not connect to MongoDB: {e}")
except Exception as e:
    print(f"An unexpected error occurred during MongoDB setup: {e}")

def save_lead(lead_data: dict):
    """Saves the initial lead document after phone number submission."""
    if collection is None:
        print("ERROR: Cannot save lead, no database collection available.")
        return False
    try:
        # Use update_one with upsert=True to avoid duplicates if the user restarts
        collection.update_one(
            {"email": lead_data["email"]},
            {"$set": lead_data},
            upsert=True
        )
        print(f"Successfully saved initial lead for {lead_data['email']}")
        return True
    except Exception as e:
        print(f"Error saving lead to MongoDB: {e}")
        return False

def update_lead_details(email: str, full_details: dict):
    """Finds a lead by email and updates it with all collected details."""
    if collection is None:
        print("ERROR: Cannot update lead, no database collection available.")
        return False
    try:
        result = collection.update_one(
            {"email": email},
            {"$set": full_details}
        )
        if result.modified_count > 0 or result.upserted_id is not None:
            print(f"Successfully updated full details for {email}.")
        return True
    except Exception as e:
        print(f"Error updating lead in MongoDB: {e}")
        return False