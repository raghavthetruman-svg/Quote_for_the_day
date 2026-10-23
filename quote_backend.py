import asyncio
import re
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError


class Quote(BaseModel):
    id: int = Field(gt=0)
    quote: str = Field(min_length=1)
    author: str = Field(min_length=1)


app = FastAPI()


async def fetch_quote() -> Quote:
    """Fetch one random quote and validate its JSON data."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("https://dummyjson.com/quotes/random")
        response.raise_for_status()
        return Quote.model_validate(response.json())


@app.get("/quote", response_model=Quote)
async def get_quote() -> Quote:
    """Return a validated random quote, or a friendly upstream error."""
    try:
        return await fetch_quote()
    except (httpx.HTTPError, ValidationError) as error:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch a quote. Please try again.",
        ) from error


@app.get("/quote/stream")
async def stream_quote() -> StreamingResponse:
    """Stream a fetched quote one word at a time."""
    try:
        quote = await fetch_quote()
    except (httpx.HTTPError, ValidationError) as error:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch a quote. Please try again.",
        ) from error

    message = f'"{quote.quote}" - {quote.author}'

    async def generate_words() -> AsyncIterator[str]:
        words = list(re.finditer(r"\S+\s*", message))
        for index, word in enumerate(words):
            if index > 0:
                await asyncio.sleep(0.1)
            yield word.group()

    return StreamingResponse(generate_words(), media_type="text/plain")


async def main() -> None:
    quote = await fetch_quote()
    print(quote.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())