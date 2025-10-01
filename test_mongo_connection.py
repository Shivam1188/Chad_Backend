import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

MONGO_URL = "mongodb+srv://devex_db_user:t4OJrfUwXNGdPFkV@cluster1.eazct4k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
DB_NAME = "chad_Muraw_db"

async def test_connection():
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        await db.command("ping")
        print("✅ Successfully connected to MongoDB")
        client.close()
    except PyMongoError as e:
        print(f"❌ Could not connect to MongoDB: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
