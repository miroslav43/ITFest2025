#!/usr/bin/env python
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
import ast
# Import utility functions
from utils import cosine_similarity

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
HCL_CSV_PATH = "data/hcl_summarized_with_embeddings.csv"
SERVICE_CSV_PATH = "data/ServicesEmbedings.csv"

# Global variables to store data
hcl_data = None
service_data = None

def load_csv_data():
    """
    Load data from CSV files into global variables.
    This function should be called at the start of the FastAPI application.
    """
    global hcl_data, service_data
    
    logger.info("Loading data from CSV files...")
    
    # Load HCL data
    try:
        hcl_df = pd.read_csv(HCL_CSV_PATH)
        logger.info(f"Loaded {len(hcl_df)} HCL records from {HCL_CSV_PATH}")
        
        # Convert string embeddings to lists if needed using ast.literal_eval
        if 'embedings' in hcl_df.columns and isinstance(hcl_df['embedings'].iloc[0], str):
            hcl_df['embedings'] = hcl_df['embedings'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        
        # Convert DataFrame to list of dictionaries for easier manipulation
        hcl_data = hcl_df.to_dict('records')
        
        # Add unique IDs if not present
        for i, doc in enumerate(hcl_data):
            if '_id' not in doc:
                doc['_id'] = str(i)
    except Exception as e:
        logger.error(f"Error loading HCL data: {e}")
        hcl_data = []
    
    # Load Service data
    try:
        service_df = pd.read_csv(SERVICE_CSV_PATH)
        logger.info(f"Loaded {len(service_df)} service records from {SERVICE_CSV_PATH}")
        
        # Convert string embeddings to lists if needed using ast.literal_eval
        if 'embedings' in service_df.columns and isinstance(service_df['embedings'].iloc[0], str):
            service_df['embedings'] = service_df['embedings'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        
        # Convert DataFrame to list of dictionaries for easier manipulation
        service_data = service_df.to_dict('records')
        
        # Add unique IDs if not present
        for i, doc in enumerate(service_data):
            if '_id' not in doc:
                doc['_id'] = str(i)
    except Exception as e:
        logger.error(f"Error loading service data: {e}")
        service_data = []
    
    logger.info("Data loading complete")

def vector_search(collection_type: str, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Performs a vector search using the embedding field.
    
    Args:
        collection_type (str): The type of collection to search ('hcl' or 'service').
        embedding (List[float]): The query embedding vector.
        limit (int): The maximum number of documents to return.
        
    Returns:
        List[Dict[str, Any]]: A list of matching documents.
    """
    if collection_type.lower() == 'hcl':
        data = hcl_data
    elif collection_type.lower() == 'service':
        data = service_data
    else:
        logger.error(f"Invalid collection type: {collection_type}")
        return []
    
    # Calculate cosine similarity for each document
    docs_with_scores = []
    
    for doc in data:
        if "embedings" in doc and doc["embedings"]:
            score = cosine_similarity(embedding, doc["embedings"])
            docs_with_scores.append((doc, score))
    
    # Sort by similarity score (descending)
    docs_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get the top documents
    top_docs = [doc for doc, _ in docs_with_scores[:limit]]
    
    return top_docs

def search_hcl_documents(query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Searches for HCL documents based on a query.
    
    Args:
        query (Dict[str, Any]): The search query.
        limit (int): The maximum number of documents to return.
        
    Returns:
        List[Dict[str, Any]]: A list of matching HCL documents.
    """
    results = []
    
    for doc in hcl_data:
        match = True
        for key, value in query.items():
            if key not in doc or doc[key] != value:
                match = False
                break
        
        if match:
            results.append(doc)
            if len(results) >= limit:
                break
    
    return results

def search_service_documents(query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Searches for service documents based on a query.
    
    Args:
        query (Dict[str, Any]): The search query.
        limit (int): The maximum number of documents to return.
        
    Returns:
        List[Dict[str, Any]]: A list of matching service documents.
    """
    results = []
    
    for doc in service_data:
        match = True
        for key, value in query.items():
            if key not in doc or doc[key] != value:
                match = False
                break
        
        if match:
            results.append(doc)
            if len(results) >= limit:
                break
    
    return results

def main():
    """
    Main function to load data from CSV files.
    """
    load_csv_data()
    logger.info("CSV data loaded successfully")

if __name__ == "__main__":
    main()