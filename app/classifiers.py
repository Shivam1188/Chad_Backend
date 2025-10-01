import openai
import json
from app.prompts import POST_CLASSIFICATION_PROMPT, PROFILE_CLASSIFICATION_PROMPT
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)

CLASSIFICATION_MODEL = "gpt-4o"

# Thread pool for OpenAI calls
executor = ThreadPoolExecutor(max_workers=5)

def _classify_post_sync(post_text: str) -> dict:
    """Synchronous classification for post."""
    try:
        prompt = POST_CLASSIFICATION_PROMPT.format(post_text=post_text)
        logger.info(f"Sending prompt: {prompt}")
        response = openai.chat.completions.create(
            model=CLASSIFICATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        logger.info(f"Response received: {response}")
        result_text = response.choices[0].message.content
        if result_text:
            result_text = result_text.strip()
            logger.info(f"GPT response for post: '{result_text}'")
            # Parse the format: sentiment: ..., theme: ..., format_suitability: ...
            try:
                parts = result_text.split(', ')
                sentiment = parts[0].split(': ')[1].strip('[]')
                theme = parts[1].split(': ')[1].strip('[]')
                format_suitability = parts[2].split(': ')[1].strip('[]')
                return {"sentiment": sentiment, "theme": theme, "format_suitability": format_suitability}
            except (IndexError, ValueError) as e:
                logger.error(f"Failed to parse response: {e}, response: '{result_text}'")
                return {"sentiment": "unknown", "theme": "unknown", "format_suitability": "unknown"}
        else:
            logger.error("Empty response from GPT")
            return {"sentiment": "unknown", "theme": "unknown", "format_suitability": "unknown"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for post: {e}, response: '{result_text}'")
        return {"sentiment": "unknown", "theme": "unknown", "format_suitability": "unknown"}
    except Exception as e:
        logger.error(f"Error classifying post: {e}")
        return {"sentiment": "unknown", "theme": "unknown", "format_suitability": "unknown"}

def _classify_profile_sync(profile_text: str) -> str:
    """Synchronous classification for profile."""
    try:
        prompt = PROFILE_CLASSIFICATION_PROMPT.format(profile_text=profile_text)
        response = openai.chat.completions.create(
            model=CLASSIFICATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        logger.error(f"Error classifying profile: {e}")
        return "Unknown profile type"

async def classify_post(post_text: str) -> dict:
    """Classify a post for sentiment, theme, and format suitability."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _classify_post_sync, post_text)

async def classify_profile(profile_text: str) -> str:
    """Classify a user profile into a descriptive phrase."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _classify_profile_sync, profile_text)
