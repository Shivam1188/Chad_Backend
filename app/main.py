from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app.models.sheet_request import SheetRequest
from app.database import db, connect_to_mongo, close_mongo_connection, get_sheet_metadata, update_sheet_metadata
from app.routers.classification import router as classification_router
from app.routers.content_generation import router as content_generation_router
import openai
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import time
import logging
from dataclasses import dataclass
import hashlib
import json
import uuid
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import subprocess


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(classification_router, prefix="/classification", tags=["classification"])
app.include_router(content_generation_router, prefix="/content-generation", tags=["content-generation"])

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_scrapping_scripts, 'interval', hours=6)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    if 'scheduler' in globals():
        scheduler.shutdown()

SERVICE_ACCOUNT_FILE = "service_account.json"
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, scope
)
gc = gspread.authorize(credentials)

# --- OpenAI setup ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# GPT-4o model for classification
CLASSIFICATION_MODEL = "gpt-4o"

# Configuration for parallel processing
MAX_WORKERS = 10
BATCH_SIZE = 100
EMBEDDING_BATCH_SIZE = 20
PINECONE_BATCH_SIZE = 100

@dataclass
class ProcessingStats:
    total_records: int = 0
    processed_records: int = 0
    inserted_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    start_time: float = 0
    
    def get_progress(self) -> float:
        return (self.processed_records / self.total_records * 100) if self.total_records > 0 else 0

# Thread pool executor
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# --- Utility functions ---
def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize a single record"""
    cleaned = {}
    for k, v in record.items():
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean:
                cleaned[k] = v_clean
        elif v is not None:
            cleaned[k] = v
    return cleaned

def get_record_hash(record: Dict[str, Any]) -> str:
    """Generate a hash for a record to check for duplicates efficiently"""
    record_str = json.dumps(record, sort_keys=True, default=str)
    return hashlib.md5(record_str.encode()).hexdigest()

def is_public_record(record: Dict[str, Any]) -> bool:
    """Check if a record contains only public data (GDPR/CCPA compliance)"""
    # Define fields that indicate personal or non-public data
    personal_fields = ['email', 'phone', 'ssn', 'credit_card', 'personal_id', 'full_name', 'user_id']
    # Check if any personal field is present and not empty
    for field in personal_fields:
        if field in record and record[field]:
            return False
    # Additional checks can be added here (e.g., consent flags, data source verification)
    return True

async def run_scrapping_scripts():
    scripts = ['Scrapping/perfumes.py', 'Scrapping/reddit.py', 'Scrapping/stockists.py']
    tasks = []
    for script in scripts:
        # Run each script in parallel using subprocess
        tasks.append(asyncio.create_subprocess_exec('python', script, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error running {scripts[i]}: {result}")
        else:
            stdout, stderr = await result.communicate()
            if stderr:
                logger.error(f"Stderr for {scripts[i]}: {stderr.decode()}")
            logger.info(f"Completed running {scripts[i]}")



async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts in a single API call"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: openai.embeddings.create(
                model="text-embedding-3-large",
                input=texts[:EMBEDDING_BATCH_SIZE]
            )
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Error getting embeddings: {e}")
        # Fallback to individual embeddings
        embeddings = []
        for text in texts:
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda t=text: openai.embeddings.create(
                        model="text-embedding-3-large",
                        input=t
                    )
                )
                embeddings.append(response.data[0].embedding)
            except Exception as individual_error:
                logger.error(f"Error getting individual embedding for text: {text[:100]}...: {individual_error}")
                embeddings.append(None)  # Use None to indicate failure
        return embeddings

async def process_record_batch(
    collection, 
    records: List[Dict[str, Any]], 
    sheet_name: str,
    full_collection_name: str,
    stats: ProcessingStats
) -> List[Dict[str, Any]]:
    """Process a batch of records with cleaning and deduplication"""
    processed_records = []

    # --- Data cleaning ---
    cleaned_records = [clean_record(r) for r in records]

    # --- Deduplicate within batch ---
    unique_hashes = set()
    deduped_records = []
    for record in cleaned_records:
        record_hash = get_record_hash(record)
        if record_hash not in unique_hashes:
            record['_record_hash'] = record_hash
            deduped_records.append(record)
            unique_hashes.add(record_hash)

    if not deduped_records:
        stats.skipped_records += len(records)
        stats.processed_records += len(records)
        return processed_records

    try:
        # Check existing records in MongoDB
        record_hashes = [r['_record_hash'] for r in deduped_records]
        existing_hashes = set()
        existing_docs = collection.find({'_record_hash': {'$in': record_hashes}})
        async for doc in existing_docs:
            if '_record_hash' in doc:
                existing_hashes.add(doc['_record_hash'])

        # Filter out records already in DB
        new_records = [r for r in deduped_records if r['_record_hash'] not in existing_hashes]
        if not new_records:
            stats.skipped_records += len(records)
            stats.processed_records += len(records)
            return processed_records

        # Prepare texts for embeddings
        texts_to_embed = [" | ".join(f"{k}: {v}" for k, v in r.items() if k != "_record_hash") for r in new_records]

        # Get embeddings in batches
        all_embeddings = []
        for i in range(0, len(texts_to_embed), EMBEDDING_BATCH_SIZE):
            batch_texts = texts_to_embed[i:i+EMBEDDING_BATCH_SIZE]
            batch_embeddings = await get_embeddings_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)

        # Insert into MongoDB
        insert_result = await collection.insert_many(new_records)
        inserted_ids = insert_result.inserted_ids

        # Prepare vectors for Pinecone
        vectors_to_upsert = []
        for i, (record, embedding) in enumerate(zip(new_records, all_embeddings)):
            metadata = record.copy()
            metadata["_id"] = str(inserted_ids[i])
            metadata["sheet_name"] = sheet_name
            metadata["collection_name"] = full_collection_name
            metadata.pop('_record_hash', None)
            vectors_to_upsert.append({
                "id": str(inserted_ids[i]),
                "values": embedding,
                "metadata": metadata
            })
            processed_records.append({
                "mongo_id": str(inserted_ids[i]),
                "pinecone_vector": vectors_to_upsert[-1]
            })

        stats.inserted_records += len(new_records)
        stats.skipped_records += len(records) - len(new_records)
        stats.processed_records += len(records)
        return processed_records

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        stats.failed_records += len(records)
        stats.processed_records += len(records)
        return []

async def upsert_to_pinecone_batch(vectors: List[Dict], index):
    """Upsert vectors to Pinecone in batches"""
    try:
        for i in range(0, len(vectors), PINECONE_BATCH_SIZE):
            batch = vectors[i:i+PINECONE_BATCH_SIZE]
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda b=batch: index.upsert(vectors=b)
            )
        logger.info(f"Successfully upserted {len(vectors)} vectors to Pinecone")
    except Exception as e:
        logger.error(f"Error upserting to Pinecone: {e}")
        raise

# --- Pinecone setup ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX_NAME = "minnewyork"
EMBEDDING_DIMENSION = 3072

try:
    if INDEX_NAME in pc.list_indexes().names():
        index_info = pc.describe_index(INDEX_NAME)
        if index_info.dimension != EMBEDDING_DIMENSION:
            pc.configure_index(INDEX_NAME, deletion_protection="disabled")
            time.sleep(2)
            pc.delete_index(INDEX_NAME)
            pc.create_index(
                name=INDEX_NAME,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
    else:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    index = pc.Index(INDEX_NAME)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Pinecone index setup failed: {str(e)}")

# --- API Endpoints ---
@app.post("/import-sheet/")
async def import_sheet(request: SheetRequest):
    try:
        start_time = time.time()
        sh = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: gc.open_by_url(request.sheet_url)
        )
        worksheets = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: sh.worksheets()
        )

        overall_stats = ProcessingStats(start_time=start_time)
        sheet_summaries = {}
        all_vectors_for_pinecone = []

        for worksheet in worksheets:
            sheet_name = worksheet.title.strip().replace(" ", "_")

            # Get current sheet metadata
            metadata = await get_sheet_metadata(request.sheet_url, worksheet.title)
            last_processed_row = metadata.get("last_row_count", 0) if metadata else 0

            # Get all records from the sheet
            all_records = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: worksheet.get_all_records()
            )

            # Filter for public records only (GDPR/CCPA compliance)
            public_all_records = [r for r in all_records if is_public_record(r)]

            # Insert raw data into "Sheet Raw Data" collection with deduplication
            raw_collection = db["Sheet Raw Data"]
            raw_docs = []
            for record in public_all_records:
                raw_doc = {
                    **record,
                    "sheet_url": request.sheet_url,
                    "worksheet_title": worksheet.title,
                    "imported_at": time.time()
                }
                # Generate hash for deduplication based on record content + identifiers
                hash_content = {
                    **record,
                    "sheet_url": request.sheet_url,
                    "worksheet_title": worksheet.title
                }
                record_str = json.dumps(hash_content, sort_keys=True, default=str)
                raw_doc['_record_hash'] = hashlib.md5(record_str.encode()).hexdigest()
                raw_docs.append(raw_doc)

            # Check for existing records
            existing_hashes = set()
            if raw_docs:
                record_hashes = [doc['_record_hash'] for doc in raw_docs]
                existing_docs = raw_collection.find({'_record_hash': {'$in': record_hashes}})
                async for doc in existing_docs:
                    existing_hashes.add(doc['_record_hash'])

            # Insert only new records
            new_raw_docs = [doc for doc in raw_docs if doc['_record_hash'] not in existing_hashes]
            if new_raw_docs:
                await raw_collection.insert_many(new_raw_docs)

            # Determine which records to process
            if request.force_reprocess:
                records = public_all_records
                logger.info(f"Force reprocessing all public records for sheet {sheet_name}")
            else:
                # Only process new records since last processed row
                new_records = all_records[last_processed_row:] if last_processed_row < len(all_records) else []
                records = [r for r in new_records if is_public_record(r)]
                if not records:
                    logger.info(f"No new public records found for sheet {sheet_name}")
                    continue

            full_collection_name = request.collection + "_" + sheet_name
            collection = db[full_collection_name]
            sheet_stats = ProcessingStats(total_records=len(records), start_time=time.time())

            tasks = []
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i+BATCH_SIZE]
                tasks.append(process_record_batch(collection, batch, sheet_name, full_collection_name, sheet_stats))
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            sheet_vectors = []
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    continue
                for item in result:
                    if 'pinecone_vector' in item:
                        sheet_vectors.append(item['pinecone_vector'])

            if sheet_vectors:
                await upsert_to_pinecone_batch(sheet_vectors, index)
                all_vectors_for_pinecone.extend(sheet_vectors)

            # Update overall stats
            
            overall_stats.total_records += sheet_stats.total_records
            overall_stats.processed_records += sheet_stats.processed_records
            overall_stats.inserted_records += sheet_stats.inserted_records
            overall_stats.skipped_records += sheet_stats.skipped_records
            overall_stats.failed_records += sheet_stats.failed_records

            sheet_summaries[sheet_name] = {
                "total_records": sheet_stats.total_records,
                "inserted_records": sheet_stats.inserted_records,
                "skipped_records": sheet_stats.skipped_records,
                "failed_records": sheet_stats.failed_records,
                "processing_time": time.time() - sheet_stats.start_time
            }

            # Update metadata with new last processed row count
            if request.force_reprocess:
                new_last_row_count = len(all_records)
            else:
                new_last_row_count = last_processed_row + len(records)
            await update_sheet_metadata(request.sheet_url, worksheet.title, new_last_row_count)

        total_time = time.time() - start_time
        if overall_stats.total_records == 0:
            raise HTTPException(status_code=404, detail="No data found in any sheet")

        return {
            "message": "Data imported successfully with cleaning & deduplication (incremental processing)",
            "summary": {
                "total_records": overall_stats.total_records,
                "inserted_records": overall_stats.inserted_records,
                "skipped_records": overall_stats.skipped_records,
                "failed_records": overall_stats.failed_records,
                "vectors_in_pinecone": len(all_vectors_for_pinecone),
                "total_processing_time": total_time,
                "average_records_per_second": overall_stats.total_records / total_time if total_time > 0 else 0,
                "force_reprocess": request.force_reprocess
            },
            "sheet_details": sheet_summaries
        }
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# --- Search & stats endpoints remain unchanged ---
@app.get("/search/")
async def search(query: str, top_k: int = 5, sheet_name: str = None):
    try:
        query_embedding = await get_embeddings_batch([query])
        filter_dict = {"sheet_name": {"$eq": sheet_name}} if sheet_name else None
        results = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
        )
        return {"query": query, "results": results.to_dict(), "total_matches": len(results.matches) if hasattr(results, 'matches') else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/stats/")
async def get_index_stats():    
    try:
        stats = await asyncio.get_event_loop().run_in_executor(executor, lambda: index.describe_index_stats())
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.delete("/clear-index/")
async def clear_index():
    try:
        await asyncio.get_event_loop().run_in_executor(executor, lambda: index.delete(delete_all=True))
        return {"message": "Index cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")

@app.delete("/reset-sheet-metadata/")
async def reset_sheet_metadata(sheet_url: str):
    """Reset the processing metadata for a specific sheet"""
    try:
        from app.database import sheet_metadata
        result = await sheet_metadata.delete_one({"sheet_url": sheet_url})
        if result.deleted_count > 0:
            return {"message": f"Metadata reset for sheet {sheet_url}"}
        else:
            return {"message": f"No metadata found for sheet {sheet_url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset metadata: {str(e)}")

@app.websocket("/ws/auto-import")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for client message or send periodic updates
            data = await websocket.receive_text()

            if data == "start_auto_import":
                # Start automatic import process
                await websocket.send_text("Starting automatic import process...")

                # Run the import process in a loop
                while True:
                    try:
                        # Create the request payload
                        request_data = {
                            "sheet_url": "https://docs.google.com/spreadsheets/d/1TYyaIYOgfsTV-ZfktfL7n-ln6mOlOL9m0bKRfyiIkjc/edit?gid=0#gid=0",
                            "collection": "sheet_data"
                        }

                        # Call the import function
                        result = await import_sheet_internal(request_data)

                        # Send result back to client
                        await websocket.send_text(f"Import completed: {result}")

                        # Wait for 30 seconds before next import (adjust as needed)
                        await asyncio.sleep(30)

                    except Exception as e:
                        await websocket.send_text(f"Error during import: {str(e)}")
                        await asyncio.sleep(30)

            elif data == "stop":
                await websocket.send_text("Stopping automatic import process")
                break

    except WebSocketDisconnect:
        print("WebSocket disconnected")

async def import_sheet_internal(request_data: dict):
    """Internal function to call the import logic"""
    try:
        # Create a mock SheetRequest object
        request = SheetRequest(**request_data)

        # Reuse the existing import logic
        start_time = time.time()
        sh = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: gc.open_by_url(request.sheet_url)
        )
        worksheets = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: sh.worksheets()
        )

        overall_stats = ProcessingStats(start_time=start_time)
        sheet_summaries = {}
        all_vectors_for_pinecone = []

        for worksheet in worksheets:
            sheet_name = worksheet.title.strip().replace(" ", "_")

            # Get current sheet metadata
            metadata = await get_sheet_metadata(request.sheet_url, worksheet.title)
            last_processed_row = metadata.get("last_row_count", 0) if metadata else 0

            # Get all records from the sheet
            all_records = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: worksheet.get_all_records()
            )

            # Filter for public records only (GDPR/CCPA compliance)
            public_all_records = [r for r in all_records if is_public_record(r)]

            # Insert raw data into "Sheet Raw Data" collection with deduplication
            raw_collection = db["Sheet Raw Data"]
            raw_docs = []
            for record in public_all_records:
                 raw_doc = {
                     **record,
                     "sheet_url": request.sheet_url,
                     "worksheet_title": worksheet.title,
                     "imported_at": time.time()
                 }
                 # Generate hash for deduplication based on record content + identifiers
                 hash_content = {
                     **record,
                     "sheet_url": request.sheet_url,
                     "worksheet_title": worksheet.title
                 }
                 record_str = json.dumps(hash_content, sort_keys=True, default=str)
                 raw_doc['_record_hash'] = hashlib.md5(record_str.encode()).hexdigest()
                 raw_docs.append(raw_doc)

            # Check for existing records
            existing_hashes = set()
            if raw_docs:
                record_hashes = [doc['_record_hash'] for doc in raw_docs]
                existing_docs = raw_collection.find({'_record_hash': {'$in': record_hashes}})
                async for doc in existing_docs:
                    existing_hashes.add(doc['_record_hash'])

            # Insert only new records
            new_raw_docs = [doc for doc in raw_docs if doc['_record_hash'] not in existing_hashes]
            if new_raw_docs:
                await raw_collection.insert_many(new_raw_docs)

            # Determine which records to process
            if getattr(request, 'force_reprocess', False):
                records = all_records
                logger.info(f"Force reprocessing all records for sheet {sheet_name}")
            else:
                # Only process new records since last processed row
                new_records = all_records[last_processed_row:] if last_processed_row < len(all_records) else []
                if not new_records:
                    logger.info(f"No new records found for sheet {sheet_name}")
                    continue
                records = new_records

            full_collection_name = request.collection + "_" + sheet_name
            collection = db[full_collection_name]
            sheet_stats = ProcessingStats(total_records=len(records), start_time=time.time())

            tasks = []
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i+BATCH_SIZE]
                tasks.append(process_record_batch(collection, batch, sheet_name, full_collection_name, sheet_stats))
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            sheet_vectors = []
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    continue
                for item in result:
                    if 'pinecone_vector' in item:
                        sheet_vectors.append(item['pinecone_vector'])

            if sheet_vectors:
                await upsert_to_pinecone_batch(sheet_vectors, index)
                all_vectors_for_pinecone.extend(sheet_vectors)

            # Update overall stats
            overall_stats.total_records += sheet_stats.total_records
            overall_stats.processed_records += sheet_stats.processed_records
            overall_stats.inserted_records += sheet_stats.inserted_records
            overall_stats.skipped_records += sheet_stats.skipped_records
            overall_stats.failed_records += sheet_stats.failed_records

            sheet_summaries[sheet_name] = {
                "total_records": sheet_stats.total_records,
                "inserted_records": sheet_stats.inserted_records,
                "skipped_records": sheet_stats.skipped_records,
                "failed_records": sheet_stats.failed_records,
                "processing_time": time.time() - sheet_stats.start_time
            }

            # Update metadata with new last processed row count
            if getattr(request, 'force_reprocess', False):
                new_last_row_count = len(all_records)
            else:
                new_last_row_count = last_processed_row + len(records)
            await update_sheet_metadata(request.sheet_url, worksheet.title, new_last_row_count)

        total_time = time.time() - start_time
        if overall_stats.total_records == 0:
            return "No data found in any sheet"

        return {
            "message": "Data imported successfully with cleaning & deduplication (incremental processing)",
            "summary": {
                "total_records": overall_stats.total_records,
                "inserted_records": overall_stats.inserted_records,
                "skipped_records": overall_stats.skipped_records,
                "failed_records": overall_stats.failed_records,
                "vectors_in_pinecone": len(all_vectors_for_pinecone),
                "total_processing_time": total_time,
                "average_records_per_second": overall_stats.total_records / total_time if total_time > 0 else 0,
                "force_reprocess": getattr(request, 'force_reprocess', False)
            },
            "sheet_details": sheet_summaries
        }
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")



