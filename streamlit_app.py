import json

import httpx
import streamlit as st
from pydantic import ValidationError

from quote_backend import Quote


BACKEND_URL = "http://localhost:8000/quote"
STREAM_BACKEND_URL = "http://localhost:8000/quote/stream"
ERROR_MESSAGE = "Could not fetch a quote. Please try again."

st.title("Quote of the Day")

if st.button("Get a quote"):
    with st.spinner("Getting a quote..."):
        try:
            response = httpx.get(BACKEND_URL, timeout=10.0)
            response.raise_for_status()
            quote = Quote.model_validate(response.json())
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError):
            st.error(ERROR_MESSAGE)
        else:
            st.write(quote.quote)
            st.caption(quote.author)

if st.button("Stream a quote"):
    with st.spinner("Streaming a quote..."):
        try:
            with httpx.stream("GET", STREAM_BACKEND_URL, timeout=10.0) as response:
                response.raise_for_status()
                st.write_stream(response.iter_text())
        except httpx.HTTPError:
            st.error(ERROR_MESSAGE)