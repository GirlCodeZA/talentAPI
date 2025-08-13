from fastapi import APIRouter, HTTPException
import httpx
import asyncio
from app.settings import settings
from app.models.careerCoach import QueryRequest

career_coach_router = APIRouter()

@career_coach_router.post("/highwind/query", tags=["Career Coach"])
async def send_query_to_highwind(query_request: QueryRequest):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": settings.highwind_api_key,
    }

    payload = {
        "session_id": query_request.session_id,
        "query": query_request.query
    }

    try:
        # Step 1: Send query to Highwind
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            initial_response = await client.post(
                f"{settings.highwind_api_url}/queries",
                headers=headers,
                json=payload
            )

        initial_response.raise_for_status()
        chat_id = initial_response.json().get("chat_id")

        if not chat_id:
            raise HTTPException(status_code=502, detail="Missing chat_id in response")

        # Step 2: Poll for chat result
        response_data = None
        max_attempts = 10
        wait_interval = 10  # seconds between polls

        for attempt in range(max_attempts):
            query_url = f"{settings.highwind_api_url}/queries/?chat_id={chat_id}"
            print(f"Polling attempt {attempt + 1}: {query_url}")  # Optional debug log

            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                chat_response = await client.get(query_url, headers=headers)

            try:
                chat_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

            chat_json = chat_response.json()

            if chat_json.get("status") == "SUCCEEDED":
                response_data = chat_json
                break

            await asyncio.sleep(wait_interval)

        if not response_data:
            raise HTTPException(
                status_code=504,
                detail=f"Timed out waiting for Highwind query response after {max_attempts * wait_interval} seconds"
            )

        return {
            "chat_id": chat_id,
            "status": response_data.get("status"),
            "response": response_data.get("response"),
            "evaluation_table": response_data.get("evaluation_table")
        }

    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="Highwind API timed out")

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
