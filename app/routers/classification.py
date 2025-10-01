from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.classifiers import classify_post, classify_profile

router = APIRouter()

class PostClassificationRequest(BaseModel):
    post_text: str

class ProfileClassificationRequest(BaseModel):
    profile_text: str

@router.post("/classify-post/")
async def classify_post_endpoint(request: PostClassificationRequest):
    """Classify a post for sentiment, theme, and format suitability."""
    try:
        result = await classify_post(request.post_text)
        return {"classification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@router.post("/classify-profile/")
async def classify_profile_endpoint(request: ProfileClassificationRequest):
    """Classify a user profile."""
    try:
        result = await classify_profile(request.profile_text)
        return {"classification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
