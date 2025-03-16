from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import uvicorn

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials securely
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

def get_response(question, content):
    prompt = """
    Tu esti un asistent virtual menit sa raspunda la intrebarile venite de la public. Raspunsurile trebuie sa fie bazate pe continutul acesta:
    """
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt + content},
            {"role": "user", "content": question}
        ]
    )
    return chat_completion.choices[0].message.content

app = FastAPI()

# Set up CORS to allow any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # acceptă orice origine
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
