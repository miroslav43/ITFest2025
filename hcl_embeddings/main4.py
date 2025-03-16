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

# Configurable parameters
TOP_K = 3
# Use GPU if available
device_emb = "cuda:0" if torch.cuda.is_available() else "cpu"

# Load the sentence transformer model for similarity computations
sim_model = SentenceTransformer("Alibaba-NLP/gte-Qwen2-7B-instruct", trust_remote_code=True).to(device_emb)

# Load precomputed embeddings and texts from .npy files
hcl_embeddings_matrix = np.load('hcl_embeddings.npy')
hcl_texts = np.load('hcl_texts.npy', allow_pickle=True)
servicii_embeddings_matrix = np.load('servicii_embeddings.npy')
servicii_texts = np.load('servicii_texts.npy', allow_pickle=True)

print("NPY embeddings and texts loaded successfully.")

def normalize(embeddings):
    """Normalize embeddings row-wise."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms

# Normalize embeddings
hcl_embeddings_norm = normalize(hcl_embeddings_matrix).astype('float32')
servicii_embeddings_norm = normalize(servicii_embeddings_matrix).astype('float32')

HCLS_PROMPT_TEMPLATE = (
    "<Întrebarea: {question}>\n"
    "Raspunde pe baza acestui context: {docs}"
)

SERVICII_PROMPT_TEMPLATE = (
    "Întrebarea: {question}\n"
    "Raspunde pe baza acestui context: {docs}"
)

FUSION_PROMPT_TEMPLATE = (
    "Întrebarea: {question}\n"
    "Raspunde la intrebare pe baza acestui context {servicii_response}\n{hcls_response}"
)

@app.get("/provide_response")
def provide_response(question: str = Query(..., description="Întrebarea pentru care se dorește răspunsul bazat pe context.")):
    # Compute the embedding for the input question
    question_embedding = sim_model.encode([question], convert_to_numpy=True, device=device_emb)
    question_embedding_norm = normalize(question_embedding).astype('float32')
    
    # Compute cosine similarities
    hcl_similarities = cosine_similarity(question_embedding_norm, hcl_embeddings_norm)[0]
    servicii_similarities = cosine_similarity(question_embedding_norm, servicii_embeddings_norm)[0]
    
    # Get the top-K indices for both sources
    hcl_top_indices = np.argsort(hcl_similarities)[::-1][:TOP_K]
    servicii_top_indices = np.argsort(servicii_similarities)[::-1][:TOP_K]
    
    # Retrieve top-K document texts
    hcl_docs_str = "\n\n".join([hcl_texts[int(idx)] for idx in hcl_top_indices])
    servicii_docs_str = "\n\n".join([servicii_texts[int(idx)] for idx in servicii_top_indices])
    
    # Create prompts for each source
    hcls_prompt = HCLS_PROMPT_TEMPLATE.format(docs=hcl_docs_str, question=question)
    servicii_prompt = SERVICII_PROMPT_TEMPLATE.format(docs=servicii_docs_str, question=question)
    
    # Generate responses using GPT-4o
    hcls_response = get_response(question, hcls_prompt)
    servicii_response = get_response(question, servicii_prompt)
    
    # Generate a final fused response
    fusion_prompt = FUSION_PROMPT_TEMPLATE.format(
        question=question,
        servicii_response=servicii_response,
        hcls_response=hcls_response,
    )
    final_response = get_response(question, fusion_prompt)
    
    return {
        "question": question,
        "hcls_response": hcls_response,
        "servicii_response": servicii_response,
        "final_response": final_response,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)