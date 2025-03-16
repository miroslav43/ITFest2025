#!/usr/bin/env python3

import os
import ssl
import json
import ast
import math
import urllib.request
import time
import pickle
import logging

import pandas as pd
from tqdm.auto import tqdm
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

# Setup logging for detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
ENDPOINT_URL = os.getenv("ENDPOINT_URL")

if not API_KEY or "CHEIA_TA_API" in API_KEY:
    raise Exception("API_KEY is not set correctly in .env. Please check API_KEY!")
if not ENDPOINT_URL:
    raise Exception("ENDPOINT_URL is not set in .env!")

# Allow self-signed HTTPS certificates if needed (e.g., in test environments)

def allow_self_signed_https(allow: bool) -> None:
    if allow and not os.environ.get('PYTHONHTTPSVERIFY', '') and hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

allow_self_signed_https(True)

# Utility function to calculate cosine similarity between two vectors

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension.")
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

# Function to get embeddings from the API with retry logic

def get_embeddings(texts, endpoint_url, api_key, max_retries=5):
    """
    Sends a request to the embeddings endpoint for a list of texts and returns a list of embedding vectors.
    Retries up to max_retries times if a 429 (rate limit) error is encountered.
    """
    data = {"input": texts}
    body = json.dumps(data).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    req = urllib.request.Request(endpoint_url, data=body, headers=headers)
    retries = 0
    while retries < max_retries:
        try:
            with urllib.request.urlopen(req) as response:
                result = response.read().decode("utf-8")
                json_result = json.loads(result)
                embeddings = [item["embedding"] for item in json_result["data"]]
                return embeddings
        except urllib.error.HTTPError as error:
            if error.code == 429:
                retry_after = int(error.headers.get("Retry-After", "10"))
                logging.warning(f"Received 429 error. Retry-After: {retry_after} seconds. Attempt {retries+1}/{max_retries}.")
                time.sleep(retry_after)
                retries += 1
            else:
                logging.error("Request failed with status code: %s", error.code)
                logging.error("Headers: %s", error.info())
                try:
                    error_response = error.read().decode("utf-8")
                except Exception:
                    error_response = "No error response available."
                logging.error("Error response: %s", error_response)
                return []
    logging.error("Maximum retries reached. Failed to obtain embeddings.")
    return []
