import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from dotenv import load_dotenv
import certifi
from datetime import datetime

load_dotenv()

# Renamed variable for clarity, though not strictly necessary
MONGO_URI = os.getenv("MONGO_URI") 
DATABASE_NAME = "vingsfire_leads"
COLLECTION_NAME = "proposals"

client = None
collection = None

try:
    if not MONGO_URI:
        raise ConfigurationError("MONGO_URI environment variable is not set.")
    
    # Use certifi to provide SSL certificate
    ca = certifi.where()
    client = MongoClient(MONGO_URI, tlsCAFile=ca)
    
    # The ping command is a lightweight way to verify the connection.
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
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
    
def update_lead_with_resume(email: str, resume_path: str):
    """
    Finds a lead by email and adds or updates their resume file path.
    """
    # Add robust check for database connection
    if collection is None:
        print("ERROR: Cannot update lead with resume, no database collection available.")
        return
        
    try:
        # --- BUG FIX: Use the correct global variable 'collection' ---
        collection.update_one(
            {"email": email},
            {"$set": {"resume_path": resume_path, "last_updated": datetime.utcnow()}},
            upsert=False # We don't want to create a new lead if they don't exist
        )
        print(f"--- MongoDB: Added resume path '{resume_path}' for lead {email} ---")
    except Exception as e:
        print(f"--- MongoDB ERROR: Could not update lead with resume path. Error: {e} ---")