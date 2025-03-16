from fastapi import FastAPI, Query
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

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

# Configurable parameters
TOP_K = 3
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

# Normalize embeddings (if not already normalized)
hcl_embeddings_norm = normalize(hcl_embeddings_matrix).astype('float32')
servicii_embeddings_norm = normalize(servicii_embeddings_matrix).astype('float32')

GENERAL_GUIDELINES = (
    "In prima parte a raspunsului sa fie rescrisa in intrebarea, iar mai apoi sa vina raspunsul incepand cu urmatorul rand. "
    "Raspunsul final sa aiba o structura care sa fie usor inteleasa si citita de orice user. "
    "Mentine in raspunsul final explicit și complet denumirea exactă, numărul/anul și articolele precise ale tuturor actelor legislative și regulamentelor relevante (exemplu: O.G. nr.99/2000, H.G. nr.1739/2006, Legea nr.61/1991, Legea nr.215/2001 art.36 alin.(4) lit.e, alin.(6) lit.a pct.7 și 11, H.C.L. nr.102/2009, H.C.L. nr.290/2022, O.U.G. nr.57/2019). "
    "Mentine in raspunsul final toate linkurile care apar in context fara sa modifici in niciun fel aceste linkuri (exemplu: https://www.primariatm.ro/hcl/2009/155, https://servicii.primariatm.ro/dfmt-pj-declararea-instrainarii-terenurilor). "
    "Selectează explicit și strict articolele care pot ajuta la raspunsul unei intrebari care aprobă, abrogă sau modifică direct conținutul legislativ, indicatorii tehnico-economici sau regulamentele existente. "
    "Nu utiliza diacritice, caractere speciale sau spații excesive. "
    "Nu adăuga observații, comentarii personale sau precizări suplimentare care nu ajută la răspunderea întrebării."
)

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
    "Raspunde la intrebare pe baza acest context {servicii_response}\n{hcls_response}"
)

@app.get("/provide_response")
def provide_response(question: str = Query(..., description="Întrebarea pentru care se dorește răspunsul bazat pe context.")):
    # Compute the embedding for the input question using the similarity model
    question_embedding = sim_model.encode([question], convert_to_numpy=True, device=device_emb)
    question_embedding_norm = normalize(question_embedding).astype('float32')
    
    # Compute cosine similarities for both HCLS and Servicii embeddings
    hcl_similarities = cosine_similarity(question_embedding_norm, hcl_embeddings_norm)[0]
    servicii_similarities = cosine_similarity(question_embedding_norm, servicii_embeddings_norm)[0]
    
    # Get the top-K indices for both sources
    hcl_top_indices = np.argsort(hcl_similarities)[::-1][:TOP_K]
    servicii_top_indices = np.argsort(servicii_similarities)[::-1][:TOP_K]
    
    # Retrieve top-K document texts and build context strings
    hcl_docs_str = "\n\n".join([hcl_texts[int(idx)] for idx in hcl_top_indices])
    servicii_docs_str = "\n\n".join([servicii_texts[int(idx)] for idx in servicii_top_indices])
    
    # Create prompts for each source using their templates
    hcls_prompt = HCLS_PROMPT_TEMPLATE.format(docs=hcl_docs_str, question=question)
    servicii_prompt = SERVICII_PROMPT_TEMPLATE.format(docs=servicii_docs_str, question=question)
    
    # Generate responses using GPT (Azure OpenAI)
    hcls_response = get_response(question, hcls_prompt)
    servicii_response = get_response(question, servicii_prompt)
    
    # Generate a final fused response folosind ambele răspunsuri parțiale
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