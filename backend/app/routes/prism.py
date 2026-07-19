"""
prism.py — Main PRISM analysis route.

POST /api/prism/analyze accepts a PrismRequest and returns a PrismResponse.
The route handler contains NO business logic — it only validates input, calls
the service layer, handles exceptions, and returns the response.
This separation means the service can be tested independently of HTTP.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import PrismRequest, PrismResponse
from app.services.prism_service import PrismService
from app.middleware.auth_middleware import get_current_user_id
from app.utils.logger import get_logger

router = APIRouter(tags=["prism"])
logger = get_logger(__name__)


@router.post("/prism/analyze", response_model=PrismResponse)
async def analyze(
    request: PrismRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Run the full PRISM analysis for a user's purchase context.

    Detects the life event, runs a 4-agent debate, computes a confidence score,
    generates temporal strategies, and returns a complete culturally-aware
    purchase recommendation.

    **Example input:**
    ```json
    {
      "user_input": "my son got into IIT Bombay, need hostel essentials",
      "user_pincode": "400076",
      "budget": 50000
    }
    ```
    """
    logger.info(f"Analysis request received: '{request.user_input[:50]}...'")
    try:
        service = PrismService(db)
        result = await service.analyze(request, user_id=user_id)
        logger.info(
            f"Analysis complete: event={result.event_key}, "
            f"score={result.confidence.total_score}"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis failed. Please ensure GROQ_API_KEY is set and valid. "
                f"Error: {str(e)}"
            ),
        )
