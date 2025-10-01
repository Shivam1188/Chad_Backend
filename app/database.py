import os
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

MONGO_URL = "mongodb+srv://devex_db_user:t4OJrfUwXNGdPFkV@cluster1.eazct4k.mongodb.net/"
DB_NAME = "chad_Muraw_db"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collection for tracking sheet processing metadata
sheet_metadata = db["sheet_metadata"]


async def connect_to_mongo():
    try:
        await db.command("ping")
        print("✅ Successfully connected to MongoDB")
    except PyMongoError as e:
        print("❌ Could not connect to MongoDB:", e)


async def close_mongo_connection():
    client.close()
    print("🔌 MongoDB connection closed")


async def get_sheet_metadata(sheet_url: str, worksheet_title: str):
    """Get the last processed state for a sheet and worksheet"""
    return await sheet_metadata.find_one({"sheet_url": sheet_url, "worksheet_title": worksheet_title})


async def update_sheet_metadata(sheet_url: str, worksheet_title: str, last_row_count: int):
    """Update the last processed row count for a sheet and worksheet"""
    await sheet_metadata.update_one(
        {"sheet_url": sheet_url, "worksheet_title": worksheet_title},
        {"$set": {"sheet_url": sheet_url, "worksheet_title": worksheet_title, "last_row_count": last_row_count, "last_updated": time.time()}},
        upsert=True
    )
