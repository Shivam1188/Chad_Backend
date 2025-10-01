import openai
import json
from app.prompts import BLOG_GENERATION_PROMPT, SOCIAL_SNIPPET_GENERATION_PROMPT, B2B_EMAIL_GENERATION_PROMPT
from pinecone import Pinecone
import os
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging

logger = logging.getLogger(__name__)

GENERATION_MODEL = "gpt-4o"

# Thread pool for OpenAI calls
executor = ThreadPoolExecutor(max_workers=5)

# Pinecone setup
pc = Pinecone(api_key="pcsk_6WvWws_9ibWmA81ab7QEN65iWvHHSMo231Bg8zoacEw1feaJh75mmUMBtEoCsdyL9BYuXN")
index = pc.Index("minnewyork")

def _generate_content_sync(prompt: str) -> str:
    """Synchronous content generation."""
    try:
        logger.info(f"Sending prompt for generation")
        response = openai.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,  # Adjust based on content type
            temperature=0.7
        )
        result_text = response.choices[0].message.content
        if result_text:
            return result_text.strip()
        else:
            logger.error("Empty response from GPT")
            return "Error: No content generated"
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return f"Error: {str(e)}"

async def _search_pinecone(query: str, top_k: int = 5) -> str:
    """Search Pinecone and format results."""
    try:
        # Get embedding for query
        embedding_response = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: openai.embeddings.create(
                model="text-embedding-3-large",
                input=[query]
            )
        )
        query_embedding = embedding_response.data[0].embedding

        # Search Pinecone
        results = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
        )

        # Format data
        data_parts = []
        if hasattr(results, 'matches'):
            for match in results.matches:
                metadata = match.metadata
                data_str = ", ".join(f"{k}: {v}" for k, v in metadata.items() if k not in ['_id', 'sheet_name', 'collection_name'])
                data_parts.append(data_str)
        formatted_data = "\n".join(data_parts)
        return formatted_data
    except Exception as e:
        logger.error(f"Error searching Pinecone: {e}")
        return ""

async def generate_blog(query: str) -> str:
    """Generate a blog post based on query."""
    data = await _search_pinecone(query, top_k=10)  # More data for blog
    prompt = BLOG_GENERATION_PROMPT.format(query=query, data=data)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _generate_content_sync, prompt)

async def generate_social_snippet(query: str) -> str:
    """Generate a social media snippet."""
    data = await _search_pinecone(query, top_k=5)
    prompt = SOCIAL_SNIPPET_GENERATION_PROMPT.format(query=query, data=data)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _generate_content_sync, prompt)

async def generate_b2b_email(query: str) -> str:
    """Generate a B2B pitch email."""
    data = await _search_pinecone(query, top_k=5)
    prompt = B2B_EMAIL_GENERATION_PROMPT.format(query=query, data=data)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _generate_content_sync, prompt)
