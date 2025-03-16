#!/usr/bin/env python3

import os
import logging
import json
from typing import List, Dict, Any, Optional
import ast

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager


# Import utility functions
from utils import get_embeddings, cosine_similarity

import csv_data
from csv_data import search_hcl_documents, search_service_documents, vector_search

# Define collection names for compatibility
HCL_COLLECTION = "hcl_documents"
SERVICE_COLLECTION = "service_documents"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
API_KEY_SERV = os.getenv("API_KEY_SERV")
ENDPOINT_URL_SERV = os.getenv("ENDPOINT_URL_SERV")


API_KEY_4O=os.getenv("API_KEY_4o")
ENDPOINT_URL_4O=os.getenv("ENDPOINT_URL_4o")
API_VERSION = os.getenv("API_VERSION")

# Initialize global variables for data
cached_hcl_docs = []
cached_service_docs = []

def answer_query_with_cosine(query: str, collection_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
    global cached_hcl_docs, cached_service_docs  # Declare globals at the very beginning
    logger.info(f"Processing query with cosine similarity: {query}")
    endpoint, api_key = (ENDPOINT_URL, API_KEY) if collection_name == HCL_COLLECTION else (ENDPOINT_URL_SERV, API_KEY_SERV)
    
    query_embedding_list = get_embeddings([query], endpoint, api_key)
    if not query_embedding_list:
        logger.error("Failed to obtain embedding for the query.")
        return []
    query_embedding = query_embedding_list[0]
    # print(f"mere:::",query_embedding)

    # Make sure data is loaded
    if not cached_hcl_docs and not cached_service_docs:
        csv_data.load_csv_data()  
        cached_hcl_docs = csv_data.hcl_data.copy() if csv_data.hcl_data else []
        cached_service_docs = csv_data.service_data.copy() if csv_data.service_data else []

    # Use cached documents based on the collection_name
    all_docs = cached_hcl_docs if collection_name == HCL_COLLECTION else cached_service_docs
    docs_with_scores = []
    for doc in all_docs:
        embedding = doc.get("embedings")
        print("pere:",embedding)
        if not embedding or not isinstance(embedding, list):
            logger.warning(f"Skipping document {doc.get('_id')}: embedding type is {type(embedding)}, expected list")
            continue
        try:
            score = cosine_similarity(query_embedding, embedding)
            docs_with_scores.append((doc, score))
        except Exception as e:
            logger.warning(f"Error calculating similarity for document {doc.get('_id')}: {e}")

    docs_with_scores.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in docs_with_scores[:top_k]]

def get_best_hcl(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Return a list of best HCL documents based on the query.
    
    Args:
        query (str): The query text.
        top_k (int): The number of top results to return.
        
    Returns:
        List[Dict[str, Any]]: A list of top matching HCL documents.
    """
    return answer_query_with_cosine(query, HCL_COLLECTION, top_k)

def get_hcl_content(hcl_docs: List[Dict[str, Any]]) -> str:
    """
    Extract and format content from HCL documents.
    
    Args:
        hcl_docs (List[Dict[str, Any]]): A list of HCL documents.
        
    Returns:
        str: Formatted content from the HCL documents.
    """
    content = []
    for doc in hcl_docs:
        hcl_text = f"HCL: {doc.get('HCL', 'N/A')}\n"
        hcl_text += f"Data adoptării: {doc.get('dataAdoptarii', 'N/A')}\n"
        hcl_text += f"Motivație și articole: {doc.get('motivatie_articole', 'N/A')}\n\n"
        content.append(hcl_text)
    
    return "\n".join(content)

# Functions for Services data
def get_best_services(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Return a list of best service documents based on the query.
    
    Args:
        query (str): The query text.
        top_k (int): The number of top results to return.
        
    Returns:
        List[Dict[str, Any]]: A list of top matching service documents.
    """
    return answer_query_with_cosine(query, SERVICE_COLLECTION, top_k)

def get_service_content(service_docs: List[Dict[str, Any]]) -> str:
    """
    Extract and format content from service documents.
    
    Args:
        service_docs (List[Dict[str, Any]]): A list of service documents.
        
    Returns:
        str: Formatted content from the service documents.
    """
    content = []
    for doc in service_docs:
        service_text = f"Service ID: {doc.get('service_id', 'N/A')}\n"
        service_text += f"Name: {doc.get('name', 'N/A')}\n"
        service_text += f"URL: {doc.get('url', 'N/A')}\n"
        service_text += f"Lista mentiuni: {doc.get('Lista_mentiuni', 'N/A')}\n"
        service_text += f"Querry HCL: {doc.get('QuerryHCL', 'N/A')}\n"
        service_text += f"Service text: {doc.get('Service_text', 'N/A')}\n\n"
        content.append(service_text)
    
    return "\n".join(content)

# Function to get a response using Azure OpenAI
def get_response(question: str, content: str) -> str:
    """
    Get a response from Azure OpenAI based on the question and content.
    
    Args:
        question (str): The user's question.
        content (str): The context content to use for answering.
        
    Returns:
        str: The response from the AI model.
    """
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=API_KEY_4O,  
            api_version=API_VERSION,
            azure_endpoint=ENDPOINT_URL_4O
        )
        
        prompt = (
            "Tu ești un asistent virtual conceput pentru a răspunde la întrebările publicului. "
            "Răspunsurile tale pot include informații numerice, cum ar fi referințe la legi sau link-uri, "
            "și trebuie să se bazeze exclusiv pe conținutul prezentat mai jos.\n\n"
        )
        
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt + content},
                {"role": "user", "content": question}
            ]
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting response from Azure OpenAI: {e}")
        return f"Error generating response: {str(e)}"

# Pydantic models for API
class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    response: str



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await load_collections()  # For example, load your MongoDB collections into memory
    yield
    # Shutdown code (if needed)

async def load_collections():
    global cached_hcl_docs, cached_service_docs
    try:
        # Load data from CSV files using the csv_data module
        csv_data.load_csv_data()
        
        # Copy data from the csv_data module's global variables
        cached_hcl_docs = csv_data.hcl_data.copy() if csv_data.hcl_data else []
        cached_service_docs = csv_data.service_data.copy() if csv_data.service_data else []
        
        logger.info(f"Cached {len(cached_hcl_docs)} HCL documents and {len(cached_service_docs)} Service documents on startup.")
    except Exception as e:
        logger.error(f"Error loading collections on startup: {e}")

app = FastAPI(
    title="ITFest 2025 API",
    description="API for answering questions based on HCL and Service data",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "ITFest 2025 API is running"}

@app.get("/askCombined", response_model=QuestionResponse)
async def ask_combined(question: str):
    """
    Ask a question and get a response based on data from both HCL and Service documents.
    
    Args:
        question (str): The user's question.
        
    Returns:
        QuestionResponse: The response from the AI model.
    """
    try:
        # Get best matches from both collections
        best_hcl_docs = get_best_hcl(question)
        best_service_docs = get_best_services(question)
        print(f"besthcl:{best_hcl_docs} \n\n\n\n bestservice:{best_service_docs}")
        if not best_hcl_docs and not best_service_docs:
            return {"response": "No relevant documents found for your question."}
        
        # Combine content from both sources
        hcl_content = get_hcl_content(best_hcl_docs)
        service_content = get_service_content(best_service_docs)
        combined_content = hcl_content + "\n\n" + service_content
        
        # Get response
        response_text = get_response(question, combined_content)
        
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Error in askCombined endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """
    Main function to run the FastAPI app using Uvicorn.
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()
