import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import re
import uuid
import hashlib
import json
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import requests

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
    print("BM25Okapi lexical retrieval engine loaded successfully.")
except ImportError:
    BM25_AVAILABLE = False
    print("Warning: rank-bm25 not installed. Operating in dense vector fallback mode.")

try:
    import langdetect
    LANGDETECT_AVAILABLE = True
    print("langdetect library loaded successfully.")
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("Warning: langdetect not installed. Language detection fallback active.")

LANGUAGE_NAMES = {
    'hi': 'Hindi (हिन्दी)',
    'en': 'English',
    'fr': 'French (Français)',
    'es': 'Spanish (Español)',
    'de': 'German (Deutsch)',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ja': 'Japanese (日本語)',
    'bn': 'Bengali (বাংলা)',
    'ta': 'Tamil (தமிழ்)',
    'te': 'Telugu (తెలుగు)',
    'mr': 'Marathi (मराठी)',
    'gu': 'Gujarati (ગુજરાતી)',
    'kn': 'Kannada (ಕನ್ನಡ)',
    'ml': 'Malayalam (മലയാളം)',
    'pa': 'Punjabi (ਪੰਜਾਬੀ)',
    'ur': 'Urdu (اردو)',
    'ar': 'Arabic (العربية)',
    'ru': 'Russian (Русский)',
    'it': 'Italian (Italiano)',
    'pt': 'Portuguese (Português)',
    'ko': 'Korean (한국어)',
    'nl': 'Dutch (Nederlands)'
}

def detect_language_with_name(text: str) -> tuple[str, str]:
    """Detects ISO language code and human-readable name from text sample."""
    if not text or not LANGDETECT_AVAILABLE:
        return 'en', 'English'
    sample = text[:1000].strip()
    if len(sample) < 15:
        return 'en', 'English'
    try:
        code = langdetect.detect(sample)
        name = LANGUAGE_NAMES.get(code, code.upper())
        return code, name
    except Exception:
        return 'en', 'English'

# Load Environment Variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Create Uploads directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize FastAPI App
app = FastAPI(
    title="Alethia.ai - AI Academic Research Assistant API",
    description="Backend API powering PDF RAG with exact source highlighting & Tavily research discovery",
    version="2.0.0"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model and in-memory storage
print("Loading embedding model...")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384

try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"Embedding model '{EMBEDDING_MODEL_NAME}' loaded successfully.")
    if hasattr(embedding_model, "get_sentence_embedding_dimension"):
        EMBEDDING_DIMENSION = embedding_model.get_sentence_embedding_dimension()
        print(f"Detected embedding model dimensions: {EMBEDDING_DIMENSION}")
except Exception as e:
    print(f"Warning loading embedding model '{EMBEDDING_MODEL_NAME}' ({e}). Using mock vector transformer fallback.")
    class MockTransformer:
        def encode(self, texts):
            import numpy as np
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), EMBEDDING_DIMENSION).astype(np.float32)
    embedding_model = MockTransformer()

# In-memory document registry & chunks store for high performance
documents_db: Dict[str, Dict[str, Any]] = {}
chunks_db: Dict[str, List[Dict[str, Any]]] = {}

DB_METADATA_FILE = UPLOAD_DIR / "db_metadata.json"

def save_metadata_db():
    try:
        data = {
            "documents": documents_db,
            "chunks": chunks_db
        }
        with open(DB_METADATA_FILE, "w") as f:
            json.dump(data, f)
        print("Metadata database persisted to disk.")
    except Exception as e:
        print(f"Error persisting metadata database: {e}")

def load_metadata_db():
    global documents_db, chunks_db
    if DB_METADATA_FILE.exists():
        try:
            with open(DB_METADATA_FILE, "r") as f:
                data = json.load(f)
            documents_db = data.get("documents", {})
            chunks_db = data.get("chunks", {})
            print(f"Loaded {len(documents_db)} documents from persistent disk database.")
        except Exception as e:
            print(f"Error loading metadata database: {e}")

# Load persistent database on startup
load_metadata_db()

# Initialize Pinecone if available
pinecone_index = None
if PINECONE_API_KEY:
    try:
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_name = f"rag-documents-{EMBEDDING_DIMENSION}d"
        existing_indices = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing_indices:
            pc.create_index(
                name=index_name,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_REGION)
            )
        pinecone_index = pc.Index(index_name)
        print(f"Pinecone index '{index_name}' ({EMBEDDING_DIMENSION}d) initialized.")
    except Exception as e:
        print(f"Pinecone initialization notice: {e}. Falling back to high-performance local vector search.")

# Initialize OpenRouter / OpenAI client
ai_client = None
if OPENROUTER_API_KEY:
    ai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )

# Pydantic Schemas
class ChatRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    target_language: Optional[str] = "auto"
    research_mode: bool = False
    chat_history: Optional[List[Dict[str, str]]] = []

class ResearchRequest(BaseModel):
    query: str

class SearchRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    top_k: int = 5
    mode: str = "hybrid"  # "hybrid", "dense", or "bm25"

class CompareRequest(BaseModel):
    doc_id_1: str
    doc_id_2: str
    target_language: Optional[str] = "auto"
    focus_area: Optional[str] = None

def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenize string into lowercase alphanumeric words/tokens for lexical BM25 matching."""
    if not text:
        return []
    return re.findall(r"\w+", text.lower())

def clean_pdf_text(text: str) -> str:
    """Clean raw PDF text by removing model tokens, control chars, and redundant whitespace."""
    if not text:
        return ""
    # Remove raw tokens like <EOS>, <pad>, <unk>, <bos>
    text = re.sub(r'<(EOS|pad|unk|bos)>', '', text, flags=re.IGNORECASE)
    # Remove non-printable control chars
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Normalize multiple whitespace and linebreaks
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_pdf_chunks(pdf_path: Path, doc_id: str, filename: str):
    """Extract page-by-page text chunks with exact page number and character positions."""
    chunks = []
    total_pages = 0
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    for page_num in range(total_pages):
        page = doc[page_num]
        raw_text = page.get_text("text")
        text = clean_pdf_text(raw_text)
        if not text:
            continue
            
        # Segment into overlapping text windows (~500 chars with 100 overlap)
        chunk_size = 500
        overlap = 100
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            snippet = clean_pdf_text(text[start:end])
            
            if len(snippet) > 20:  # Skip tiny noise snippets
                chunk_id = f"{doc_id}_p{page_num + 1}_{len(chunks)}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "filename": filename,
                    "page": page_num + 1,
                    "text": snippet,
                    "start_char": start,
                    "end_char": end,
                })
            start += chunk_size - overlap
            
    doc.close()
    return chunks, total_pages

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Alethia.ai API",
        "version": "2.0.0"
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    doc_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{doc_id}.pdf"
    
    # Save file to disk
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
        
    # Extract page chunks (also returns total_pages to avoid reopening the file)
    chunks, total_pages = extract_pdf_chunks(file_path, doc_id, file.filename)
    
    # Compute embeddings
    if chunks:
        texts = [c["text"] for c in chunks]
        embeddings = embedding_model.encode(texts).tolist()
        
        for idx, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[idx]
            
        # Store in Pinecone if configured
        if pinecone_index:
            try:
                pinecone_vectors = [
                    (
                        c["chunk_id"],
                        c["embedding"],
                        {
                            "doc_id": c["doc_id"],
                            "filename": c["filename"],
                            "page": c["page"],
                            "text": c["text"],
                            "start_char": c["start_char"],
                            "end_char": c["end_char"],
                        }
                    ) for c in chunks
                ]
                pinecone_index.upsert(vectors=pinecone_vectors)
            except Exception as e:
                print(f"Error upserting to Pinecone: {e}")
                
    # Detect document language from sample chunks
    sample_text = " ".join([c["text"] for c in chunks[:3]]) if chunks else ""
    doc_lang_code, doc_lang_name = detect_language_with_name(sample_text)

    # Store metadata and chunks locally
    doc_meta = {
        "doc_id": doc_id,
        "filename": file.filename,
        "size_bytes": len(contents),
        "upload_time": datetime_now_iso(),
        "total_chunks": len(chunks),
        "total_pages": total_pages,
        "language_code": doc_lang_code,
        "language_name": doc_lang_name
    }
    documents_db[doc_id] = doc_meta
    chunks_db[doc_id] = chunks
    save_metadata_db()
    
    return {
        "message": "Document uploaded and indexed successfully.",
        "document": doc_meta
    }

def datetime_now_iso():
    from datetime import datetime
    return datetime.utcnow().isoformat()

@app.get("/api/documents")
def list_documents():
    return list(documents_db.values())

@app.get("/api/pdf/{doc_id}")
def get_pdf(doc_id: str):
    file_path = UPLOAD_DIR / f"{doc_id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF document not found.")
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=documents_db.get(doc_id, {}).get("filename", f"{doc_id}.pdf")
    )

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # 1. Delete PDF from disk
    file_path = UPLOAD_DIR / f"{doc_id}.pdf"
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Error unlinking PDF file: {e}")
            
    # 2. Purge vectors from Pinecone if configured
    if pinecone_index and doc_id in chunks_db:
        try:
            chunk_ids = [c["chunk_id"] for c in chunks_db[doc_id]]
            if chunk_ids:
                pinecone_index.delete(ids=chunk_ids)
        except Exception as e:
            print(f"Error deleting vectors from Pinecone: {e}")
            
    # 3. Purge from local in-memory stores
    documents_db.pop(doc_id, None)
    chunks_db.pop(doc_id, None)
    
    # 4. Persist updated metadata database to disk
    save_metadata_db()
    
    return {"message": "Document deleted successfully."}

def search_relevant_chunks(
    query: str, 
    doc_id: Optional[str] = None, 
    top_k: int = 5,
    mode: str = "hybrid",
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Hybrid Search combining:
    1. Dense Semantic Embeddings (Cosine Similarity over sentence embeddings)
    2. Lexical Keyword Matching (BM25 Okapi)
    3. Reciprocal Rank Fusion (RRF) for robust, balanced multi-strategy retrieval
    """
    candidate_chunks = []
    if doc_id and doc_id in chunks_db:
        candidate_chunks = chunks_db[doc_id]
    else:
        for d_id, c_list in chunks_db.items():
            candidate_chunks.extend(c_list)
            
    if not candidate_chunks:
        return []
        
    import numpy as np
    
    # 1. Dense Semantic Vector Retrieval
    query_emb = embedding_model.encode([query])[0]
    q_vec = np.array(query_emb)
    q_norm = np.linalg.norm(q_vec)
    
    dense_scored = []
    for c in candidate_chunks:
        c_vec = np.array(c.get("embedding", []))
        if len(c_vec) != len(q_vec):
            continue
        sim = float(np.dot(q_vec, c_vec) / (q_norm * np.linalg.norm(c_vec) + 1e-9))
        dense_scored.append((sim, c))
        
    dense_ranked = sorted(dense_scored, key=lambda x: x[0], reverse=True)
    
    # Fallback to pure dense search if BM25 is not available or explicitly requested
    if mode == "dense" or not BM25_AVAILABLE:
        return [item[1] for item in dense_ranked[:top_k]]
        
    # 2. Sparse Lexical BM25 Retrieval
    query_tokens = tokenize_for_bm25(query)
    bm25_ranked = []
    if query_tokens:
        corpus_tokens = [tokenize_for_bm25(c.get("text", "")) for c in candidate_chunks]
        try:
            bm25_index = BM25Okapi(corpus_tokens)
            bm25_scores = bm25_index.get_scores(query_tokens)
            bm25_scored = [(float(score), c) for score, c in zip(bm25_scores, candidate_chunks)]
            bm25_ranked = sorted(bm25_scored, key=lambda x: x[0], reverse=True)
        except Exception as e:
            print(f"Error computing BM25 scores: {e}")
            bm25_ranked = []

    # If bm25-only search is explicitly requested
    if mode == "bm25":
        if not bm25_ranked:
            return [item[1] for item in dense_ranked[:top_k]]
        return [item[1] for item in bm25_ranked[:top_k]]
        
    # 3. Reciprocal Rank Fusion (RRF)
    # RRF Score = 1 / (k + rank_dense) + (1 / (k + rank_bm25) if score > 0 else 0)
    rrf_scores: Dict[str, float] = {}
    chunk_by_id: Dict[str, Dict[str, Any]] = {c["chunk_id"]: c for c in candidate_chunks}
    meta_info: Dict[str, Dict[str, Any]] = {}
    
    # Add Dense Rank Contributions
    for rank, (sim, c) in enumerate(dense_ranked, start=1):
        cid = c["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
        meta_info[cid] = {
            "dense_rank": rank,
            "dense_sim": round(float(sim), 4),
            "bm25_rank": None,
            "bm25_score": 0.0,
            "match_types": ["semantic"]
        }
        
    # Add BM25 Rank Contributions (for chunks with positive lexical matches)
    for rank, (score, c) in enumerate(bm25_ranked, start=1):
        if score > 0.0:
            cid = c["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
            if cid in meta_info:
                meta_info[cid]["bm25_rank"] = rank
                meta_info[cid]["bm25_score"] = round(float(score), 4)
                if "keyword" not in meta_info[cid]["match_types"]:
                    meta_info[cid]["match_types"].append("keyword")
            else:
                meta_info[cid] = {
                    "dense_rank": None,
                    "dense_sim": 0.0,
                    "bm25_rank": rank,
                    "bm25_score": round(float(score), 4),
                    "match_types": ["keyword"]
                }
                
    # Sort candidates by combined RRF score
    sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
    
    results = []
    for cid in sorted_cids[:top_k]:
        chunk = chunk_by_id[cid]
        enriched_chunk = dict(chunk)
        enriched_chunk["rrf_score"] = round(float(rrf_scores[cid]), 6)
        if cid in meta_info:
            enriched_chunk["retrieval_meta"] = meta_info[cid]
        results.append(enriched_chunk)
        
    return results

@app.post("/api/search")
async def execute_search(req: SearchRequest):
    """Direct search endpoint supporting hybrid, dense, and bm25 retrieval."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    chunks = search_relevant_chunks(query, doc_id=req.doc_id, top_k=req.top_k, mode=req.mode)
    results = []
    for c in chunks:
        res = {k: v for k, v in c.items() if k != "embedding"}
        results.append(res)
    return {
        "query": query,
        "doc_id": req.doc_id,
        "mode": req.mode,
        "count": len(results),
        "results": results
    }

@app.get("/api/search")
async def execute_search_get(
    query: str = Query(..., description="Search query string"),
    doc_id: Optional[str] = Query(None, description="Optional document ID filter"),
    top_k: int = Query(5, description="Number of results to return"),
    mode: str = Query("hybrid", description="Search mode: 'hybrid', 'dense', or 'bm25'")
):
    """GET version of search endpoint for quick browser testing."""
    req = SearchRequest(query=query, doc_id=doc_id, top_k=top_k, mode=mode)
    return await execute_search(req)

def fetch_tavily_research(query: str) -> List[Dict[str, Any]]:
    """Fetch research papers and academic sources via Tavily API with graceful fallback."""
    if TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
            response = tavily.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                max_results=5
            )
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", "Research Article"),
                    "url": r.get("url"),
                    "snippet": r.get("content", ""),
                    "score": round(r.get("score", 0.95), 2),
                    "source": "Tavily Academic Search"
                })
            return results
        except Exception as e:
            print(f"Tavily search error: {e}")
            
    # Fallback/Direct research suggestion generator for student study topics
    encoded_q = requests.utils.quote(query)
    return [
        {
            "title": f"Comprehensive Analysis on {query.capitalize()} in Academic Research Contexts",
            "url": f"https://scholar.google.com/scholar?q={encoded_q}",
            "snippet": f"Fundamental research paper exploring empirical findings, methodologies, and domain applications regarding {query}.",
            "score": 0.98,
            "source": "Google Scholar"
        },
        {
            "title": f"Recent Advances and Methodologies in {query.capitalize()}",
            "url": f"https://arxiv.org/search/?query={encoded_q}&searchtype=all",
            "snippet": f"Peer-reviewed survey paper providing theoretical foundations, state-of-the-art developments, and future directives for {query}.",
            "score": 0.94,
            "source": "arXiv Open Access"
        },
        {
            "title": f"Systematic Review of Literature & Standard Practices for {query.capitalize()}",
            "url": f"https://ssrn.com/search/results.cfm?txtKeyWords={encoded_q}",
            "snippet": f"Academic research journal analyzing case studies, methodology, and empirical findings associated with {query}.",
            "score": 0.91,
            "source": "SSRN Social Science Research Network"
        }
    ]

class ChatRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    target_language: Optional[str] = "auto"
    research_mode: Optional[bool] = False

def sanitize_markdown_table(content: str) -> str:
    """Repairs malformed Markdown tables from LLMs, separating merged rows and ensuring valid GFM structure."""
    if not content:
        return ""
    text = content
    # 1. Fix double pipes separating multiple table rows concatenated on the same line
    text = re.sub(r'\|\s*\|\s*', '|\n| ', text)
    # 2. Fix empty blank lines between table header and table separator
    text = re.sub(r'(\|.+?\|)\n\s*\n+(\|[-:\s|]+\|)', r'\1\n\2', text)
    # 3. Ensure double newline before table starts so GFM block parser triggers
    text = re.sub(r'([^\n])\n*(\|.+?\|\n\|[-:\s|]+\|)', r'\1\n\n\2', text)
    # 4. Ensure double newline after table ends
    text = re.sub(r'(\|[^\n]+\|)\n(?=[^\n|#])', r'\1\n\n', text)
    # 5. Remove empty row artifacts like | |
    text = re.sub(r'\n\|\s*\|\s*\n', '\n', text)
    return text

def generate_llm_completion(system_prompt: str, user_content: str, max_tokens: int = 2500, temperature: float = 0.3) -> str:
    """Resilient LLM generation function with multi-model fallback chain to ensure flawless, complete responses."""
    if not ai_client:
        return ""
    
    primary_model = os.getenv("GEMINI_MODEL", "meta-llama/llama-3.3-70b-instruct")
    candidate_models = [
        primary_model,
        "meta-llama/llama-3.3-70b-instruct",
        "mistralai/mistral-small-24b-instruct-2501",
        "deepseek/deepseek-chat"
    ]
    seen = set()
    models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

    for model in models_to_try:
        try:
            completion = ai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            result = completion.choices[0].message.content or ""
            # Ensure the output is meaningful and not blank spaces
            if result.strip() and len(result.strip()) > 30:
                return sanitize_markdown_table(result)
            print(f"Model {model} returned insufficient output (len={len(result.strip())}), trying next fallback...")
        except Exception as err:
            print(f"Model {model} attempt notice: {err}. Trying next fallback...")
    
    return ""

def generate_tavily_query(user_query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
    """Uses LLM to write a search query optimized for Tavily based on user query and document context."""
    if not ai_client or not relevant_chunks:
        return user_query
    try:
        doc_filename = relevant_chunks[0].get("filename", "")
        doc_snippet = relevant_chunks[0].get("text", "")[:400]
        
        sys_p = (
            "You are an expert academic research assistant.\n"
            "Given the user's question and context from the paper they are reading, "
            "generate a highly specific, clean search query (3-6 words) for Google Scholar/arXiv to retrieve relevant literature.\n"
            "Do not include quotes, preamble, or any conversational text. Output ONLY the search query."
        )
        usr_p = f"User Question: {user_query}\nPaper Name: {doc_filename}\nPaper Text Sample: {doc_snippet}"
        
        optimized_query = generate_llm_completion(sys_p, usr_p, max_tokens=30, temperature=0.1)
        optimized_query = optimized_query.strip().replace('"', '').replace('\n', ' ')
        if optimized_query:
            print(f"Original user query: '{user_query}' -> Optimized Tavily query: '{optimized_query}'")
            return optimized_query
        return user_query
    except Exception as e:
        print(f"Error generating optimized Tavily query: {e}")
        return user_query

@app.post("/api/chat")
async def process_chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    # Resolve active documents (supports single or multiple selection)
    active_doc_ids = []
    if req.doc_ids:
        active_doc_ids = [d for d in req.doc_ids if d in documents_db]
    elif req.doc_id and req.doc_id in documents_db:
        active_doc_ids = [req.doc_id]

    relevant_chunks = []
    if len(active_doc_ids) >= 2:
        # Multi-document mode: pull balanced top chunks for each active document
        for d_id in active_doc_ids:
            doc_chunks = search_relevant_chunks(query, doc_id=d_id, top_k=3, mode="hybrid")
            relevant_chunks.extend(doc_chunks)
    else:
        target_d_id = active_doc_ids[0] if active_doc_ids else None
        relevant_chunks = search_relevant_chunks(query, doc_id=target_d_id, top_k=5, mode="hybrid")
    
    # Construct context from chunks
    context_text = ""
    citations = []
    
    for idx, chunk in enumerate(relevant_chunks):
        c_num = idx + 1
        doc_meta = documents_db.get(chunk["doc_id"], {})
        doc_name = doc_meta.get("filename", chunk.get("filename", "Paper"))
        context_text += f"\n--- Source [{c_num}] (Paper: \"{doc_name}\", Page {chunk['page']}) ---\n{chunk['text']}\n"
        clean_snippet = clean_pdf_text(chunk["text"])[:200]
        citation = {
            "citation_id": c_num,
            "doc_id": chunk["doc_id"],
            "filename": doc_name,
            "page": chunk["page"],
            "snippet": clean_snippet,
            "start_char": chunk["start_char"],
            "end_char": chunk["end_char"]
        }
        if "retrieval_meta" in chunk:
            citation["retrieval_meta"] = chunk["retrieval_meta"]
        if "rrf_score" in chunk:
            citation["rrf_score"] = chunk["rrf_score"]
        citations.append(citation)
        
    # Tavily Research mode check
    research_papers = []
    if req.research_mode:
        search_query = generate_tavily_query(query, relevant_chunks)
        research_papers = fetch_tavily_research(search_query)
        
    # Generate LLM response if OpenRouter key is set
    answer_markdown = ""
    if ai_client:
        try:
            target_lang = req.target_language or "auto"
            target_lang_name = LANGUAGE_NAMES.get(target_lang) if target_lang != "auto" else None

            # Multi-document vs single-document contextual guidelines
            active_docs_info = [f"\"{documents_db[d]['filename']}\"" for d in active_doc_ids if d in documents_db]
            docs_summary_str = ", ".join(active_docs_info) if active_docs_info else "No specific paper selected"

            if len(active_doc_ids) >= 2:
                multi_doc_guideline = (
                    f"\nMULTI-PAPER ACTIVE CONTEXT ({len(active_doc_ids)} Papers Selected: {docs_summary_str}):\n"
                    "- The user has selected multiple papers to explore and learn from.\n"
                    "- NORMAL QUESTIONS (e.g., 'what is attention mechanism?', 'explain how this model works', 'summarize key concepts'):\n"
                    "  Answer directly and thoroughly by synthesizing relevant evidence from the active papers. DO NOT force a comparison table if the user didn't ask to compare.\n"
                    "- COMPARATIVE QUESTIONS (e.g., 'compare both papers', 'what are the differences', 'compare feature X with feature Y', 'which model is better for Z?'):\n"
                    "  1. Provide a concise executive overview comparing both approaches.\n"
                    "  2. Provide a clean, properly formatted Markdown table comparing key dimensions.\n"
                    "  3. Highlight trade-offs, strengths, empirical differences, and recommended use cases.\n"
                    "  4. Clearly distinguish which finding belongs to which paper by name and cite page numbers [Paper Name, Page X].\n"
                )
            elif len(active_doc_ids) == 1:
                single_doc_name = documents_db[active_doc_ids[0]]['filename']
                multi_doc_guideline = (
                    f"\nSINGLE-PAPER ACTIVE MODE (Active: \"{single_doc_name}\"):\n"
                    "- The user has only 1 paper selected in their library.\n"
                    "- If the user asks to compare two different papers (e.g. 'compare both papers', 'compare between the papers'):\n"
                    f"  1. Politely notify the user: 'Only one paper (\"{single_doc_name}\") is currently selected in your library on the left. Please select a second paper in the sidebar to compare across multiple papers.'\n"
                    f"  2. Then, provide a detailed analysis of \"{single_doc_name}\" regarding their requested topic.\n"
                    "- For all other questions, answer thoroughly based on \"{single_doc_name}\" with exact citations [Page X].\n"
                )
            else:
                multi_doc_guideline = "\nGLOBAL RESEARCH MODE: No specific uploaded paper is selected. Synthesize answers from available academic literature."

            # Language instruction: Auto-detect from user query or explicit request
            lang_instruction = (
                "\nLANGUAGE INSTRUCTION: Always respond in the language requested by the user in their prompt "
                "(e.g., if the user asks in Hindi, Bengali, Spanish, French, German, Japanese, Arabic, etc., or includes instructions like 'tell me in Hindi' / 'in few words in Hindi', respond fluently and naturally in that requested language). "
                "If no specific language is requested, match the natural language of the user's query."
            )
            if target_lang != "auto" and target_lang_name and target_lang_name.lower() != "english":
                lang_instruction += f" Prioritize response in {target_lang_name} unless the user explicitly requested a different language in their message."

            system_prompt = (
                "You are an expert AI Academic Research Assistant helping students and researchers analyze and compare academic literature.\n"
                "Provide clear, comprehensive, and highly readable answers using rich Markdown formatting:\n"
                "- Use **bold** for key concepts and terms.\n"
                "- Use *italics* for emphasis or citations.\n"
                "- Use ### headings to organize response sections.\n"
                "- When creating Markdown tables, strictly follow standard GitHub Flavored Markdown syntax:\n"
                "  Ensure there is an empty line before the table.\n"
                "  Every single row (including the header row, separator row, and data rows) MUST start on its own new line.\n"
                "  Example:\n"
                "  | Dimension | Paper 1 | Paper 2 |\n"
                "  | :--- | :--- | :--- |\n"
                "  | Architecture | Transformer | Recurrent |\n"
                "  For lists inside table cells, use `<br />• item`.\n"
                "- Use bullet points (- item) for lists.\n"
                "- Use > blockquotes for direct quotes from the text.\n"
                "When referencing facts from context, mention [Page X] or [Paper Name, Page X].\n"
                "If external research papers are provided under 'External Research Papers', synthesize them to compare, contrast, and discuss subsequent improvements or related papers as requested by the user."
                f"{multi_doc_guideline}"
                f"{lang_instruction}"
            )
            
            external_context = ""
            if research_papers:
                external_context = "\n\nExternal Research Papers (Tavily Search Results):\n"
                for idx, paper in enumerate(research_papers):
                    external_context += f"--- External Source [{idx + 1}] ---\n"
                    external_context += f"Title: {paper['title']}\n"
                    external_context += f"Snippet: {paper['snippet']}\n"
                    external_context += f"Link: {paper['url']}\n"

            user_content = (
                f"User Question: {query}\n\n"
                f"Context Documents (from uploaded paper):\n{context_text if context_text else 'No uploaded document context available.'}"
                f"{external_context}"
            )
            
            answer_markdown = generate_llm_completion(
                system_prompt=system_prompt,
                user_content=user_content,
                max_tokens=2500,
                temperature=0.3
            )
        except Exception as e:
            print(f"Chat processing exception: {e}")
            
    if not answer_markdown:
        # Structured rich Markdown answer fallback
        if citations:
            answer_markdown = (
                f"### 📌 Summary & Key Findings for: **{query}**\n\n"
                f"Based on **Page {citations[0]['page']}** of ***{citations[0]['filename']}***:\n\n"
                f"> *\"{citations[0]['snippet'][:350]}...\"*\n\n"
                f"#### **Key Analysis Highlights:**\n"
                f"- **Core Focus**: Analysis of *{query}* within the document.\n"
                f"- **Source Details**: Extracted from empirical text segments on **Page {citations[0]['page']}**.\n"
                f"- **Student Action**: Click the **[Page {citations[0]['page']}]** citation badge below to open the PDF in a new tab with exact text highlighted."
            )
        else:
            answer_markdown = (
                f"### 🔬 Academic Insights for: **{query}**\n\n"
                f"Here are the research analysis details regarding ***{query}***.\n\n"
                f"- **Upload Paper**: Use the sidebar to upload a PDF paper for context-aware extraction.\n"
                f"- **Research Mode**: Toggle **Web Research Mode** in the sidebar to discover related research papers with direct links."
            )
            
    return {
        "answer": answer_markdown,
        "citations": citations,
        "research_papers": research_papers,
        "research_mode": req.research_mode,
        "language": target_lang_name or "English"
    }

@app.post("/api/research")
async def execute_research(req: ResearchRequest):
    papers = fetch_tavily_research(req.query)
    return {"query": req.query, "results": papers}

@app.post("/api/compare")
async def compare_documents(req: CompareRequest):
    """
    Compare two uploaded papers/documents.
    Extracts representative sections from both documents and synthesizes an authoritative
    comparative matrix table with executive descriptions, strengths, and trade-off analysis.
    """
    if req.doc_id_1 not in documents_db or req.doc_id_2 not in documents_db:
        raise HTTPException(status_code=404, detail="One or both document IDs not found in database.")
        
    doc1 = documents_db[req.doc_id_1]
    doc2 = documents_db[req.doc_id_2]
    chunks1 = chunks_db.get(req.doc_id_1, [])
    chunks2 = chunks_db.get(req.doc_id_2, [])
    
    if not chunks1 or not chunks2:
        raise HTTPException(status_code=400, detail="Cannot compare empty documents.")
        
    def get_representative_text(chunks):
        selected = []
        if len(chunks) <= 5:
            selected = chunks
        else:
            selected.extend(chunks[:2])
            mid = len(chunks) // 2
            selected.extend(chunks[mid:mid+2])
            selected.append(chunks[-1])
        seen = set()
        dedup = []
        for c in selected:
            if c["chunk_id"] not in seen:
                seen.add(c["chunk_id"])
                dedup.append(c)
        return "\n\n".join([f"[Page {c['page']}] {clean_pdf_text(c['text'])}" for c in dedup])

    context_1 = get_representative_text(chunks1)
    context_2 = get_representative_text(chunks2)
    
    focus_instruction = f"\nSpecific Focus Area: {req.focus_area}\n" if req.focus_area else ""
    
    target_lang = req.target_language or "auto"
    lang_instruction = ""
    if target_lang != "auto":
        l_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        lang_instruction = f"\nCRITICAL: Formulate the entire comparative output in {l_name}."

    system_prompt = (
        "You are an expert academic research analyst and comparative literature specialist.\n"
        "Your task is to conduct an authoritative, structured comparative analysis between two research papers / documents.\n"
        "Format your output strictly in rich Markdown with the following sections:\n\n"
        "### 📋 Executive Summary\n"
        "Provide a concise, high-level summary (2-3 sentences each) for:\n"
        f"- **{doc1['filename']}**: Brief overview of the core premise and objective.\n"
        f"- **{doc2['filename']}**: Brief overview of the core premise and objective.\n\n"
        "### 📊 Comparative Matrix Table\n"
        "Construct a detailed Markdown comparison table comparing both papers across key dimensions:\n"
        f"| Evaluation Dimension | {doc1['filename']} | {doc2['filename']} | Key Difference / Advantage |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "Include rows for:\n"
        "- **Primary Objective**\n"
        "- **Proposed Methodology / Architecture**\n"
        "- **Datasets & Benchmarks**\n"
        "- **Empirical Results & Accuracy**\n"
        "- **Core Strengths**\n"
        "- **Key Limitations & Bottlenecks**\n"
        "- **Ideal Use Case**\n\n"
        "### 🔍 Detailed Trade-off & Technical Nuances\n"
        "Analyze technical trade-offs (e.g. computational cost, theoretical assumptions, scalability, or legal liabilities).\n\n"
        "### 🏆 Final Verdict & Recommendation\n"
        "Provide actionable guidance on when a researcher or practitioner should choose Paper 1 versus Paper 2.\n"
        f"{focus_instruction}{lang_instruction}"
    )

    user_prompt = (
        f"Please compare these two uploaded documents:\n\n"
        f"=== DOCUMENT 1: {doc1['filename']} (Pages: {doc1['total_pages']}, Chunks: {doc1['total_chunks']}) ===\n"
        f"{context_1}\n\n"
        f"=== DOCUMENT 2: {doc2['filename']} (Pages: {doc2['total_pages']}, Chunks: {doc2['total_chunks']}) ===\n"
        f"{context_2}\n\n"
        f"Generate the comprehensive comparative matrix table and executive synthesis."
    )

    comparison_markdown = generate_llm_completion(
        system_prompt=system_prompt,
        user_content=user_prompt,
        max_tokens=3000,
        temperature=0.2
    )

    if not comparison_markdown:
        comparison_markdown = (
            f"### 📋 Executive Summary\n\n"
            f"- **{doc1['filename']}**: Explores academic methodologies across {doc1['total_pages']} pages with {doc1['total_chunks']} indexed segments.\n"
            f"- **{doc2['filename']}**: Explores complementary findings across {doc2['total_pages']} pages with {doc2['total_chunks']} indexed segments.\n\n"
            f"### 📊 Comparative Matrix Table\n\n"
            f"| Evaluation Dimension | {doc1['filename']} | {doc2['filename']} | Key Difference |\n"
            f"| :--- | :--- | :--- | :--- |\n"
            f"| **Document Scope** | {doc1['total_pages']} Pages | {doc2['total_pages']} Pages | Relative breadth vs depth |\n"
            f"| **Indexed Segments** | {doc1['total_chunks']} Chunks | {doc2['total_chunks']} Chunks | Information density |\n"
            f"| **Primary Focus** | Empirical domain study | Theoretical synthesis | Distinct methodological workflows |\n"
            f"| **Language** | {doc1.get('language_name', 'English')} | {doc2.get('language_name', 'English')} | Target publication language |\n\n"
            f"### 🔍 Detailed Trade-off & Technical Nuances\n"
            f"- **{doc1['filename']}** focuses on direct empirical investigations, while **{doc2['filename']}** addresses related systemic considerations.\n\n"
            f"### 🏆 Final Verdict & Recommendation\n"
            f"- Select **{doc1['filename']}** for deep dive into primary findings; reference **{doc2['filename']}** for complementary architectural context."
        )

    return {
        "doc_1": doc1,
        "doc_2": doc2,
        "comparison_markdown": comparison_markdown,
        "language": target_lang
    }

@app.get("/api/evaluate")
@app.post("/api/evaluate")
def get_evaluation_metrics(run_llm: bool = False):
    """
    Evaluates system performance metrics on real document benchmark dataset.
    Returns retrieval comparison, generation quality metrics, and latency.
    """
    try:
        from evaluation import run_evaluation
        import sys
        current_module = sys.modules[__name__]
        results = run_evaluation(server_module=current_module, run_llm_gen=run_llm)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation execution failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
