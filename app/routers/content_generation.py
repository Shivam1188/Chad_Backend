from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.content_generators import generate_blog, generate_social_snippet, generate_b2b_email

router = APIRouter()

class ContentGenerationRequest(BaseModel):
    query: str

@router.post("/generate-blog/")
async def generate_blog_endpoint(request: ContentGenerationRequest):
    """Generate a blog post based on the query."""
    try:
        result = await generate_blog(request.query)
        return {"query": request.query, "content": result, "type": "blog"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blog generation failed: {str(e)}")

@router.post("/generate-social-snippet/")
async def generate_social_snippet_endpoint(request: ContentGenerationRequest):
    """Generate a social media snippet based on the query."""
    try:
        result = await generate_social_snippet(request.query)
        return {"query": request.query, "content": result, "type": "social_snippet"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Social snippet generation failed: {str(e)}")

@router.post("/generate-b2b-email/")
async def generate_b2b_email_endpoint(request: ContentGenerationRequest):
    """Generate a B2B pitch email based on the query."""
    try:
        result = await generate_b2b_email(request.query)
        return {"query": request.query, "content": result, "type": "b2b_email"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"B2B email generation failed: {str(e)}")
