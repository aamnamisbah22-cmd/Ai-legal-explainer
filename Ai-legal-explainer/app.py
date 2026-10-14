"""
AI Legal Explainer: A RAG-based Streamlit Application
======================================================

This script implements a Retrieval-Augmented Generation (RAG) system designed to
explain complex academic and scientific papers. It features a Streamlit web
interface where users can upload PDF documents and ask questions about them.

The application is built with configurability in mind, supporting multiple
embedding dimensions for vectorization.

Core Functionalities:
---------------------
1.  **Document Processing:**
    -   Handles PDF uploads through a Streamlit interface.
    -   Utilizes Google Cloud Document AI for robust text extraction from PDFs.
    -   Chunks extracted text into smaller, overlapping segments for effective retrieval.
    -   Generates vector embeddings using SentenceTransformer models.

2.  **Vector Storage and Retrieval:**
    -   Uses Pinecone as the vector database for storing and querying document embeddings.
    -   Supports configurable embedding dimensions (e.g., 384, 1024).
    -   Performs cosine similarity searches to find relevant document chunks based on user queries.

3.  **Generative AI and Language Support:**
    -   Leverages Google's Gemini 1.5 Flash model for response generation.
    -   Implements a multi-language agent that detects the user's query language and responds accordingly.
    -   Maintains conversation history for contextual responses.

4.  **User Interface and Experience:**
    -   Built with Streamlit for a clean and interactive web application.
    -   Features session management, chat history, and document management.
    -   Provides options to export conversations and clear session memory.
   
"""

import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import PyPDF2
import langdetect
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import hashlib
import uuid
from io import BytesIO
from datetime import datetime 
import json
import time
import os
import re
from dotenv import load_dotenv


# ===========================
# CONFIGURATION SECTION
# ===========================
# Load API keys from the .env file for secure access to services.
load_dotenv()

# Retrieve API keys and configuration details from environment variables.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")  # Default to us-east-1 if not set

# ===========================
# EMBEDDING CONFIGURATION
# ===========================
# This section allows you to choose the sentence transformer model for generating embeddings.
# The choice of model affects the dimensionality of the embeddings, which in turn impacts
# storage requirements and retrieval performance. Different models offer trade-offs between
# speed, size, and quality.

# Option 1: 384-dimensional multilingual embeddings (Recommended for broad language support).
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2' 
EMBEDDING_DIMENSIONS = 384

# Option 2: 384-dimensional English-focused embeddings (Faster, for English-only documents).
# EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
# EMBEDDING_DIMENSIONS = 384

# Option 3: 768-dimensional high-quality embeddings (Larger, slower, primarily for English).
# EMBEDDING_MODEL = 'all-mpnet-base-v2'
# EMBEDDING_DIMENSIONS = 768

# Check for OpenRouter API Key.
# It's crucial for enabling the AI's text generation capabilities.
if not OPENROUTER_API_KEY:
    # If the API key is not found, display an error and stop the application.
    st.error("❌ OpenRouter API key not found. Please check your .env file.")
    st.stop()

# ===========================
# STREAMLIT PAGE CONFIGURATION
# ===========================
# Set up the Streamlit page with a custom title, a wide layout for more space,
# a relevant icon, and an initially expanded sidebar for easy access to controls.
st.set_page_config(
    page_title="🔬 Research Paper AI Assistant",
    layout="wide",
    page_icon="🔬",
    initial_sidebar_state="expanded"
)

# Display the current embedding model configuration in the sidebar.
# This provides users with transparency about the system's setup.
st.sidebar.header("📊 Current Configuration")
st.sidebar.info(f"""
**Embedding Model:** {EMBEDDING_MODEL}
**Dimensions:** {EMBEDDING_DIMENSIONS}
**Index Name:** rag-documents-{EMBEDDING_DIMENSIONS}d
""")

# ===========================
# KRUTIDEV TO UNICODE CONVERTER
# ===========================
CHARS_KD = [
    "ñ","Q+Z","sas","aa",")Z","ZZ","‘","’","“","”",
    "å",  "ƒ",  "„",   "…",   "†",   "‡",   "ˆ",   "‰",   "Š",   "‹", 
    "¶+",   "d+", "[+k","[+", "x+",  "T+",  "t+", "M+", "<+", "Q+", ";+", "j+", "u+",
    "Ùk", "Ù", "ä", "–", "—","é","™","=kk","f=k",  
    "à",   "á",    "â",   "ã",   "ºz",  "º",   "í", "{k", "{", "=",  "«",   
    "Nî",   "Vî",    "Bî",   "Mî",   "<î", "|", "K", "}",
    "J",   "Vª",   "Mª",  "<ªª",  "Nª",   "Ø",  "Ý", "nzZ",  "æ", "ç", "Á", "xz", "#", ":",
    "v‚","vks",  "vkS",  "vk",    "v",  "b±", "Ã",  "bZ",  "b",  "m",  "Å",  ",s",  ",",   "_",
    "ô",  "d", "Dk", "D", "[k", "[", "x","Xk", "X", "Ä", "?k", "?",   "³", 
    "pkS",  "p", "Pk", "P",  "N",  "t", "Tk", "T",  ">", "÷", "¥",
    "ê",  "ë",   "V",  "B",   "ì",   "ï", "M+", "<+", "M",  "<", ".k", ".",    
    "r",  "Rk", "R",   "Fk", "F",  ")", "n", "/k", "èk",  "/", "Ë", "è", "u", "Uk", "U",   
    "i",  "Ik", "I",   "Q",    "¶",  "c", "Ck",  "C",  "Hk",  "H", "e", "Ek",  "E",
    ";",  "¸",   "j",    "y", "Yk",  "Y",  "G",  "o", "Ok", "O",
    "'k", "'",   "\"k",  "\"",  "”k", "”", "“k", "“", "\\k", "\\", "l", "Lk",  "L",   "g", 
    "È", "z", 
    "Ì", "Í", "Î",  "Ï",  "Ñ",  "Ò",  "Ó",  "Ô",   "Ö",  "Ø",  "Ù","Ük", "Ü",
    "‚",    "ks",   "kS",   "k",  "h",    "q",   "w",   "`",    "s",    "S",
    "a",    "¡",    "%",     "W",  "•", "·", "∙", "·", "~j",  "~", "+"," ः",
    "^", "*",  "Þ", "ß", "(", "¼", "½", "¿", "À", "¾", "A", "-", "&", "Œ", "]","~ ","@"
]

CHARS_UNICODE = [
    "॰","QZ+","sa","a","र्द्ध","Z","\"","\"","'","'",
    "०",  "१",  "२",  "३",     "४",   "५",  "६",   "७",   "८",   "९",   
    "फ़्",  "क़",  "ख़", "ख़्",  "ग़", "ज़्", "ज़",  "ड़",  "ढ़",   "फ़",  "य़",  "ऱ",  "ऩ",
    "त्त", "त्त्", "क्त",  "दृ",  "कृ","न्न","न्न्","=k","f=",
    "ह्न",  "ह्य",  "हृ",  "ह्म",  "ह्र",  "ह्",   "द्द",  "क्ष", "क्ष्", "त्र", "त्र्", 
    "छ्य",  "ट्य",  "ठ्य",  "ड्य",  "ढ्य", "द्य", "ज्ञ", "द्व",
    "श्र",  "ट्र",    "ड्र",    "ढ्र",    "छ्र",   "क्र",  "फ्र", "र्द्र",  "द्र",   "प्र", "प्र",  "ग्र", "रु",  "रू",
    "ऑ",   "ओ",  "औ",  "आ",   "अ", "ईं", "ई",  "ई",   "इ",  "उ",   "ऊ",  "ऐ",  "ए", "ऋ",
    "क्क", "क", "क", "क्", "ख", "ख्", "ग", "ग", "ग्", "घ", "घ", "घ्", "ङ",
    "चै",  "च", "च", "च्", "छ", "ज", "ज", "ज्",  "झ",  "झ्", "ञ",
    "ट्ट",   "ट्ठ",   "ट",   "ठ",   "ड्ड",   "ड्ढ",  "ड़", "ढ़", "ड",   "ढ", "ण", "ण्",   
    "त", "त", "त्", "थ", "थ्",  "द्ध",  "द", "ध", "ध", "ध्", "ध्", "ध्", "न", "न", "न्",    
    "प", "प", "प्",  "फ", "फ्",  "ब", "ब", "ब्",  "भ", "भ्",  "म",  "म", "म्",  
    "य", "य्",  "र", "ल", "ल", "ल्",  "ळ",  "व", "व", "व्",   
    "श", "श्",  "ष", "ष्", "श", "श्", "श", "श्", "ष", "ष्", "स", "स", "स्", "ह", 
    "ीं", "्र",    
    "द्द", "ट्ट","ट्ठ","ड्ड","कृ","भ","्य","ड्ढ","झ्","क्र","त्त्","श","श्",
    "ॉ",  "ो",   "ौ",   "ा",   "ी",   "ु",   "ू",   "ृ",   "े",   "ै",
    "ं",   "ँ",   "ः",   "ॅ",  "ऽ", "ऽ", "ऽ", "ऽ", "्र",  "्", "़",":",
    "‘",   "’",   "“",   "”",  ";",  "(",    ")",   "{",    "}",   "=", "।", "-", "µ", "् ", ",","् ","/"
]

KRUTIDEV_MISENCODED_HEADERS = {
    "न्दसनसम": "Volume",
    "ीेेनम": "Issue",
    "ँमिपनंपब": "February",
    "उ्रीन्त्": "PRINT",
    "ीैैन्": "ISSN",
    "उा्रीउम्ख्": "SUBJECT",
    "ीन्द्ीान्": "INDIAN",
    "्रइग््रन्ास्": "JOURNAL",
    "इँ": "OF",
    "्रम्ैम्ा्रच्ी": "RESEARCH",
    "न्द": "NO",
}

def _krutidev_to_unicode_core(text):
    if not text:
        return text

    strKtd = text

    # 1. Replace multi-character and single-character mappings
    for kd_char, uni_char in zip(CHARS_KD, CHARS_UNICODE):
        strKtd = strKtd.replace(kd_char, uni_char)

    strKtd = strKtd.replace("±", "Zं")
    strKtd = strKtd.replace("Æ", "र्f")

    # 2. Position of 'f' (chhoti i matra)
    pos_i = strKtd.find("f")
    while pos_i != -1:
        if pos_i + 1 < len(strKtd):
            char_next = strKtd[pos_i + 1]
            strKtd = strKtd[:pos_i] + char_next + "ि" + strKtd[pos_i + 2:]
            pos_i = strKtd.find("f", pos_i + 1)
        else:
            strKtd = strKtd[:pos_i] + "ि" + strKtd[pos_i + 1:]
            break

    strKtd = strKtd.replace("Ç", "fa")
    strKtd = strKtd.replace("É", "र्fa")

    # 3. Position of 'fa'
    pos_fa = strKtd.find("fa")
    while pos_fa != -1:
        if pos_fa + 2 < len(strKtd):
            char_next = strKtd[pos_fa + 2]
            strKtd = strKtd[:pos_fa] + char_next + "िं" + strKtd[pos_fa + 3:]
            pos_fa = strKtd.find("fa", pos_fa + 2)
        else:
            break

    strKtd = strKtd.replace("Ê", "ीZ")

    # 4. Fix half-letter before 'ि' (ि्)
    pos_wrong = strKtd.find("ि्")
    while pos_wrong != -1:
        if pos_wrong + 2 < len(strKtd):
            cons_next = strKtd[pos_wrong + 2]
            strKtd = strKtd[:pos_wrong] + "्" + cons_next + "ि" + strKtd[pos_wrong + 3:]
            pos_wrong = strKtd.find("ि्", pos_wrong + 2)
        else:
            break

    # 5. Position of 'Z' (reph: half-r)
    set_of_matras = "अ आ इ ई उ ऊ ए ऐ ओ औ ा ि ी ु ू ृ े ै ो ौ ं : ँ ॅ"
    pos_z = strKtd.find("Z")
    while pos_z > 0:
        prob_pos = pos_z - 1
        while prob_pos >= 0 and strKtd[prob_pos] in set_of_matras:
            prob_pos -= 1
        if prob_pos >= 0:
            cluster = strKtd[prob_pos:pos_z]
            strKtd = strKtd[:prob_pos] + "र्" + cluster + strKtd[pos_z + 1:]
        else:
            strKtd = strKtd[:pos_z] + strKtd[pos_z + 1:]
        pos_z = strKtd.find("Z")

    return strKtd

COMMON_ENGLISH_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
    'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
    'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
    'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no',
    'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
    'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
    'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
    'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
    'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these',
    'give', 'day', 'most', 'us', 'is', 'are', 'was', 'were', 'been',
    'has', 'had', 'paper', 'research', 'document', 'study', 'analysis',
    'court', 'law', 'section', 'act', 'legal', 'method', 'data', 'model'
}

KRUTIDEV_MARKERS = [
    'f[k', 'f\'k', 'f=k', 'dks', 'esa', 'gS', 'vkS', 'vks', 'Hkkjrh;',
    'izk', 'Ld', 'fL', 'Fkk', 'Fks', 'Fkh', 'djk', 'djus',
    'fy,', 'gks', 'fnz', 'jkT;', 'egk', 'lafgrk', 'vk/kkj', '[ks',
    '=kk', 'f=k', '{kk', 'pkS', 'Hkh', 'bZ', 'vkj', 'vFk', 'vU;'
]

def is_krutidev(text):
    """
    Determines if raw text is KrutiDev legacy font encoded text.
    Returns False for standard English, French, Spanish, or existing Unicode text.
    """
    if not text or not isinstance(text, str):
        return False
    # If text already contains Devanagari Unicode (\u0900-\u097F), it doesn't need conversion
    if re.search(r'[\u0900-\u097F]', text):
        return False
    
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{2,}\b', text)]
    if not words:
        return False
    
    english_word_count = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
    english_ratio = english_word_count / max(len(words), 1)
    
    # If English words are detected, it is definitely English/Latin text
    if english_word_count >= 2 or english_ratio > 0.05:
        return False
        
    # Check for KrutiDev specific letter patterns
    kd_marker_hits = sum(1 for m in KRUTIDEV_MARKERS if m in text)
    return kd_marker_hits >= 2

def convert_krutidev_to_unicode(text):
    """
    Robust KrutiDev 010 / DevLys to Devanagari Unicode converter.
    Only converts text if genuine KrutiDev font encoding is detected.
    Leaves English and other Latin text completely untouched.
    """
    if not text or not isinstance(text, str):
        return text

    # Guard: Do not convert if text is English or already Unicode
    if not is_krutidev(text):
        return text

    # Step A: Replace known KrutiDev mis-encoded English headers
    for k, v in KRUTIDEV_MISENCODED_HEADERS.items():
        text = text.replace(k, v)

    # Step B: Preserve standard English titles/keywords/URLs/emails so they don't get scrambled
    preserved = {}
    
    # 1. URLs and Emails
    url_pattern = re.compile(r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
    for match in url_pattern.finditer(text):
        url = match.group(0)
        pua_char = chr(0xE000 + len(preserved))
        preserved[pua_char] = url
        text = text.replace(url, pua_char, 1)

    # 2. Known English section headers, labels, and common terms
    en_labels = [
        "ORIGINAL RESEARCH PAPER", "RESEARCH PAPER", "ORIGINAL PAPER", "KEY WORDS:", "KEYWORDS:",
        "KEY WORDS", "KEYWORDS", "ABSTRACT", "MANAGEMENT", "Management", "INTRODUCTION", "CONCLUSION",
        "REFERENCES", "METHODOLOGY", "RESULTS", "DISCUSSION", "AUTHOR", "AUTHORS",
        "ISSN NO -", "ISSN NO", "ISSN -", "ISSN:", "ISSN", "VOLUME -", "VOLUME",
        "ISSUE -", "ISSUE", "PRINT ISSN"
    ]
    for lbl in en_labels:
        if lbl in text:
            pua_char = chr(0xE000 + len(preserved))
            preserved[pua_char] = lbl
            text = text.replace(lbl, pua_char)

    # Step C: Convert KrutiDev to Unicode
    converted = _krutidev_to_unicode_core(text)

    # Step D: Restore preserved English entities
    for pua_char, original in preserved.items():
        converted = converted.replace(pua_char, original)

    # Step E: Post-processing fixes
    converted = re.sub(r' +', ' ', converted)
    converted = converted.replace("‘‘", '"').replace("’’", '"').replace("“", '"').replace("”", '"')
    converted = converted.replace("µ", "-")
    converted = converted.replace("ण्ण्ण्", "...")

    return converted


# ===========================
# LANGUAGE HELPER FUNCTIONS
# ===========================
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
    'pt': 'Portuguese (Português)'
}

LANGUAGE_OPTIONS_LIST = [
    ("🌐 Auto-Detect (Match PDF Language)", "auto"),
    ("🇬🇧 English", "en"),
    ("🇮🇳 Hindi (हिन्दी)", "hi"),
    ("🇮🇳 Bengali (বাংলা)", "bn"),
    ("🇮🇳 Tamil (தமிழ்)", "ta"),
    ("🇮🇳 Telugu (తెలుగు)", "te"),
    ("🇮🇳 Marathi (मराठी)", "mr"),
    ("🇮🇳 Gujarati (ગુજરાતી)", "gu"),
    ("🇮🇳 Kannada (ಕನ್ನಡ)", "kn"),
    ("🇮🇳 Malayalam (മലയാളം)", "ml"),
    ("🇮🇳 Punjabi (ਪੰਜਾਬੀ)", "pa"),
    ("🇮🇳 Urdu (اردو)", "ur"),
    ("🇪🇸 Spanish (Español)", "es"),
    ("🇫🇷 French (Français)", "fr"),
    ("🇩🇪 German (Deutsch)", "de"),
    ("🇨🇳 Chinese (Simplified)", "zh-cn"),
    ("🇯🇵 Japanese (日本語)", "ja"),
    ("🇷🇺 Russian (Русский)", "ru"),
    ("🇸🇦 Arabic (العربية)", "ar"),
    ("🇵🇹 Portuguese (Português)", "pt"),
    ("🇮🇹 Italian (Italiano)", "it")
]

LANGUAGE_CODE_MAP = {display: code for display, code in LANGUAGE_OPTIONS_LIST}

def resolve_target_language(selected_option, doc_lang_code, doc_lang_name):
    """
    Resolves the final target response language code and full name based on the user's dropdown selection.
    """
    chosen_code = LANGUAGE_CODE_MAP.get(selected_option, "auto")
    if chosen_code == "auto":
        return doc_lang_code, doc_lang_name, False
    else:
        full_name = LANGUAGE_NAMES.get(chosen_code, chosen_code.upper())
        return chosen_code, full_name, True

def detect_language_with_name(text):
    """
    Detects language code and friendly name from text using script analysis and langdetect.
    """
    if not text or not str(text).strip():
        return 'en', 'English'
    try:
        clean_sample = re.sub(r'https?://\S+|www\.\S+|\[[^\]]*\]', '', str(text)).strip()
        if not clean_sample:
            return 'en', 'English'

        # Script character distribution check
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', clean_sample))
        latin_chars = len(re.findall(r'[a-zA-Z]', clean_sample))
        
        # If the sample has Latin characters and no Devanagari script, it CANNOT be Hindi/Indic script
        if latin_chars > 10 and devanagari_chars == 0:
            try:
                lang_code = langdetect.detect(clean_sample)
            except:
                lang_code = 'en'
            # Prevent false Indic predictions on short/unusual English text
            if lang_code in ['hi', 'mr', 'ne', 'bn', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'or', 'sa', 'ur']:
                lang_code = 'en'
            lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
            return lang_code, lang_name

        if devanagari_chars > 15:
            return 'hi', 'Hindi (हिन्दी)'

        lang_code = langdetect.detect(clean_sample)
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
        return lang_code, lang_name
    except:
        return 'en', 'English'



# ===========================
# DOCUMENT PROCESSOR CLASS
# ===========================
class DocumentProcessor:
    """
    Handles the entire pipeline of processing PDF documents, from text extraction to embedding generation.
    This class encapsulates the logic for:
    - Reading uploaded PDF files.
    - Using PyMuPDF to extract text content accurately.
    - Converting legacy KrutiDev Hindi text to Unicode Devanagari.
    - Splitting the extracted text into manageable, overlapping chunks.
    - Generating vector embeddings for each chunk using a SentenceTransformer model.
    - Caching extracted text to avoid redundant processing of the same document.
    """
    
    def __init__(self, model_name=EMBEDDING_MODEL):
        """
        Initializes the DocumentProcessor.

        Args:
            model_name (str): The name of the SentenceTransformer model to use for creating embeddings.
        """
        st.write(f"🔄 Initializing Document Processor with {model_name}...")
        # Load the specified pre-trained sentence transformer model.
        self.model = SentenceTransformer(model_name)
        # A simple in-memory cache to store extracted text, using the file's hash as the key.
        self.memory_cache = {}
        # Store the embedding dimensions based on the global configuration.
        self.dimensions = EMBEDDING_DIMENSIONS
        st.write(f"✅ Document Processor ready! ({self.dimensions}D embeddings)")
    
    def clear_cache(self):
        """Clears the in-memory document cache."""
        self.memory_cache.clear()
    
    def extract_text_from_pdf(self, pdf_file):
        """
        Extracts text from an uploaded PDF file with multi-layer fallback support:
        - Repairs damaged/corrupted PDF headers and structures.
        - Extracts text page by page with PyMuPDF, falling back to layout/blocks/words.
        - Recovers pages with images and attempts OCR if text is missing.
        - Falls back to PyPDF2 (lenient parsing) if PyMuPDF cannot open the stream.
        - Automatically converts legacy KrutiDev Hindi font characters to Unicode Hindi.
        Returns a list of dicts: [{'text': '...', 'page': 1}, ...]
        """
        try:
            file_content = pdf_file.read()
            if not file_content:
                st.warning("⚠️ The uploaded file is empty.")
                return []
                
            # Generate a unique hash for the file content to use as a cache key.
            file_hash = hashlib.sha256(file_content).hexdigest()
            pdf_file.seek(0)  # Reset file pointer for subsequent use.

            # Check the cache first to avoid reprocessing.
            if file_hash in self.memory_cache:
                st.info("📄 Found document in cache. Skipping extraction.")
                return self.memory_cache[file_hash]

            st.write("📄 Extracting text from PDF locally...")
            
            # Repair / normalize PDF stream: strip extraneous leading junk bytes before %PDF- if present
            pdf_start = file_content.find(b"%PDF-")
            if pdf_start > 0:
                file_content = file_content[pdf_start:]

            pages_data = []

            # --- Attempt 1: PyMuPDF with per-page error recovery & block/OCR extraction ---
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                for i, page in enumerate(doc):
                    try:
                        # Strategy A: Standard text extraction
                        raw_text = page.get_text("text").strip()
                        
                        # Strategy B: If empty or very short, try block-level extraction
                        if not raw_text or len(raw_text) < 30:
                            try:
                                blocks = page.get_text("blocks")
                                block_texts = [b[4].strip() for b in blocks if len(b) > 4 and b[4].strip()]
                                if block_texts:
                                    raw_text = "\n".join(block_texts)
                            except Exception:
                                pass
                                
                        # Strategy C: If still empty, check for images and attempt OCR
                        if not raw_text or len(raw_text) < 20:
                            try:
                                page_images = page.get_images()
                                if page_images and hasattr(page, 'get_textpage_ocr'):
                                    ocr_tp = page.get_textpage_ocr(flags=0)
                                    ocr_text = ocr_tp.extractText().strip()
                                    if ocr_text:
                                        raw_text = ocr_text
                            except Exception:
                                pass

                        if raw_text:
                            # Convert legacy KrutiDev ASCII font characters to Hindi Unicode
                            unicode_text = convert_krutidev_to_unicode(raw_text)
                            if unicode_text and unicode_text.strip():
                                pages_data.append({"text": unicode_text.strip(), "page": i + 1})
                    except Exception as page_err:
                        # Individual corrupted page or image object should not fail other pages
                        continue
                doc.close()
            except Exception as fitz_err:
                pass

            # --- Attempt 2: PyPDF2 Fallback if PyMuPDF failed or found no text ---
            if not pages_data:
                try:
                    st.info("🔧 Attempting deep file recovery parser (PyPDF2)...")
                    reader = PyPDF2.PdfReader(BytesIO(file_content), strict=False)
                    for i, page in enumerate(reader.pages):
                        try:
                            extracted = page.extract_text()
                            if extracted and extracted.strip():
                                unicode_text = convert_krutidev_to_unicode(extracted.strip())
                                if unicode_text and unicode_text.strip():
                                    pages_data.append({"text": unicode_text.strip(), "page": i + 1})
                        except Exception:
                            continue
                except Exception as pypdf_err:
                    pass

            # Handle cases where no text is extracted.
            if not pages_data:
                st.warning("⚠️ No readable text could be extracted from this PDF. It may be a scanned image without an embedded text layer or severely corrupted.")
                return []

            # Cache the extracted text for future use.
            self.memory_cache[file_hash] = pages_data
            st.success(f"✅ Successfully extracted and processed text from {len(pages_data)} pages.")
            return pages_data
        except Exception as e:
            import traceback
            st.error(f"❌ Failed to process document locally: {str(e)}")
            st.code(traceback.format_exc())
            return []

    
    def chunk_text(self, pages_data, chunk_size=1000, overlap=200):
        """
        Splits text into chunks while preserving page numbers.
        Returns a list of dicts: [{'text': '...', 'page': 1}, ...]
        """
        st.write("✂️ Splitting text into chunks...")
        chunks = []
        
        for page_data in pages_data:
            text = page_data['text']
            page_num = page_data['page']
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                chunks.append({"text": chunk, "page": page_num})
                start = end - overlap
        
        st.success(f"✅ Created {len(chunks)} chunks")
        return chunks
    
    def create_embeddings(self, texts):
        """
        Converts a list of text chunks into their corresponding vector embeddings.

        Embeddings are dense numerical vectors that capture the semantic meaning of the text.
        These are crucial for performing similarity searches in the vector database.

        Args:
            texts (list): A list of text strings to be embedded.

        Returns:
            list: A list of embedding vectors. Returns an empty list on failure.
        """
        try:
            if not texts:
                st.warning("⚠️ No text provided for embedding creation")
                return []
            
            # Ensure that we only process non-empty text chunks.
            valid_texts = [text for text in texts if text.strip()]
            if len(valid_texts) != len(texts):
                st.warning(f"⚠️ Filtered out {len(texts) - len(valid_texts)} empty text chunks")
            
            if not valid_texts:
                st.error("❌ No valid text chunks to process")
                return []
            
            st.write(f"🔢 Creating {self.dimensions}D embeddings for {len(valid_texts)} chunks...")
            with st.spinner("Generating embeddings..."):
                # Encode the texts into embeddings using the pre-loaded model.
                embeddings = self.model.encode(valid_texts, show_progress_bar=False).tolist()
            st.success(f"✅ Created {len(embeddings)} {self.dimensions}D embeddings")
            return embeddings
        except Exception as e:
            st.error(f"❌ Failed to create embeddings: {str(e)}")
            return []

# ===========================
# PINECONE HANDLER CLASS
# ===========================
class PineconeHandler:
    """
    Manages all interactions with the Pinecone vector database.
    This class is responsible for:
    - Establishing a connection to Pinecone.
    - Ensuring the required index exists, creating it if necessary.
    - Upserting (uploading) document embeddings and their associated metadata.
    - Querying the index to find the most relevant document chunks for a given user query.
    """
    
    def __init__(self, dimensions=EMBEDDING_DIMENSIONS):
        """
        Initializes the PineconeHandler.

        Args:
            dimensions (int): The dimensionality of the embeddings to be stored in the index.
        """
        if not PINECONE_API_KEY:
            st.error("❌ Pinecone API key not found. Please check your .env file.")
            st.stop()
            
        st.write("🔄 Connecting to Pinecone...")
        
        try:
            # Initialize the Pinecone client with the API key.
            self.pc = Pinecone(api_key=PINECONE_API_KEY)
            self.dimensions = dimensions
            # Define a unique name for the index based on the embedding dimensions.
            self.index_name = f"rag-documents-{dimensions}d"
            # Ensure that the index exists before proceeding.
            self._ensure_index_exists()
            st.write(f"✅ Pinecone connection established! (Index: {self.index_name})")
        except Exception as e:
            st.error(f"❌ Failed to connect to Pinecone: {str(e)}")
            st.error("Please check your Pinecone API key and try again.")
            st.stop()
        
    def _ensure_index_exists(self):
        """
        Checks if the target Pinecone index exists, and creates it if it does not.
        This ensures that we can always connect to a valid index.
        """
        try:
            # Get a list of all existing index names.
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            # If the index does not exist, create it.
            if self.index_name not in existing_indexes:
                st.write(f"🏗️ Creating new Pinecone index with {self.dimensions} dimensions...")
                
                # Define the index configuration.
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimensions,
                    metric="cosine",  # Use cosine similarity for semantic search.
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=PINECONE_REGION
                    )
                )
                # Wait for the index to be fully provisioned by checking its status.
                st.write("⏳ Waiting for Pinecone index to be ready...")
                wait_time = 0
                max_wait_time = 60  # Maximum wait time of 60 seconds
                while wait_time < max_wait_time:
                    try:
                        index_description = self.pc.describe_index(self.index_name)
                        if index_description.status.state == 'Ready':
                            st.write(f"✅ Pinecone index is ready after {wait_time} seconds!")
                            break
                        else:
                            time.sleep(5)
                            wait_time += 5
                            st.write(f"⏳ Still waiting... ({wait_time}s elapsed)")
                    except Exception as e:
                        # If there's an error checking status, wait and try again
                        time.sleep(5)
                        wait_time += 5
                if wait_time >= max_wait_time:
                    st.warning("⚠️ Index creation is taking longer than expected. Proceeding anyway.")
                st.success(f"✅ Pinecone index created! ({self.dimensions}D)")
            else:
                st.write(f"✅ Using existing Pinecone index ({self.dimensions}D)")
            
            # Get a handle to the index object for performing operations.
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            st.error(f"❌ Failed to create/connect to Pinecone index: {str(e)}")
            raise
    
    def upsert_vectors(self, vectors, chunks, file_name):
        """
        Uploads vectors and their associated metadata to the Pinecone index.

        Args:
            vectors (list): A list of embedding vectors.
            chunks (list): The corresponding text chunks (dicts with 'text' and 'page').
            file_name (str): The name of the source document.
        """
        try:
            st.write(f"💾 Storing {len(vectors)} vectors ({self.dimensions}D) in Pinecone...")
            
            # Structure the data in the format required by Pinecone.
            vectors_to_upsert = [
                {
                    "id": f"{hashlib.md5(f'{file_name}_{i}'.encode()).hexdigest()}",  # Create a unique ID for each vector.
                    "values": vector,
                    "metadata": {
                        "text": chunk['text'][:1000],  # Store the text chunk (truncated to avoid size limits).
                        "source": file_name,
                        "page": chunk['page'],
                        "timestamp": datetime.now().isoformat(),
                        "dimensions": self.dimensions
                    }
                }
                for i, (vector, chunk) in enumerate(zip(vectors, chunks))
            ]
            
            # Upsert the vectors in batches to avoid overwhelming the API.
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
                
            st.success(f"✅ Stored {len(vectors_to_upsert)} vectors in Pinecone")
        except Exception as e:
            st.error(f"❌ Failed to store vectors: {str(e)}")
            raise
    
    def query_vectors(self, query_vector, top_k=3, filter_source=None):
        """
        Queries the Pinecone index to find vectors similar to the query vector.

        Args:
            query_vector (list): The embedding vector of the user's query.
            top_k (int): The number of top similar results to retrieve.
            filter_source (str, optional): If provided, filters the search to a specific source document.

        Returns:
            A Pinecone query result object containing the matched vectors and their metadata.
        """
        try:
            st.write("🔍 Searching for relevant documents...")
            
            # Create a metadata filter if a specific source document is selected.
            query_filter = None
            if filter_source:
                query_filter = {"source": {"$eq": filter_source}}
                st.info(f"📄 Filtering results for document: {filter_source}")
            else:
                st.info("🌐 Searching across all documents")
            
            # Define the parameters for the Pinecone query.
            query_params = {
                "vector": query_vector,
                "top_k": top_k,
                "include_metadata": True  # We need the metadata to get the original text.
            }
            
            # Add the filter to the query if it exists.
            if query_filter is not None:
                query_params["filter"] = query_filter
            
            # Execute the query.
            results = self.index.query(**query_params)
            
            st.success(f"✅ Found {len(results.matches)} relevant matches")
            return results
        except Exception as e:
            st.error(f"❌ Failed to search vectors: {str(e)}")
            # Return a mock empty result object to prevent the app from crashing on error.
            from types import SimpleNamespace
            return SimpleNamespace(matches=[])

# ===========================
# OPENROUTER HANDLER CLASS
# ===========================
class OpenRouterHandler:
    """
    Handles interactions with the OpenRouter AI models.
    This class is responsible for:
    - Initializing the OpenAI client with OpenRouter's endpoint.
    - Sending prompts and chat history to the model and receiving generated responses.
    """
    
    def __init__(self):
        """
        Initializes the OpenRouterHandler.
        """
        st.write("🔄 Initializing OpenRouter AI...")
        # Use openrouter/free by default or replace with your preferred model
        self.model = "openrouter/free"
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        st.write(f"✅ OpenRouter AI ready! (Model: {self.model})")
    
    def get_response(self, prompt, session_messages=None):
        """
        Generates a response from the OpenRouter model, maintaining conversational context.

        Args:
            prompt (str): The user's input prompt (includes context).
            session_messages (list, optional): The existing chat history.

        Returns:
            str: The text response generated by the model.
        """
        try:
            api_messages = []
            
            # Reconstruct chat history for the API
            if session_messages:
                for msg in session_messages:
                    if msg["role"] in ["user", "assistant"]:
                        # Exclude any custom keys like 'timestamp' or 'language'
                        api_messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Append the current prompt
            api_messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            # Provide a user-friendly error message if the API call fails.
            error_msg = f"Error generating response: {str(e)}"
            st.error(error_msg)
            return error_msg


# ===========================
# INITIALIZATION FUNCTION
# ===========================
@st.cache_resource
def initialize_system():
    """
    Initializes and caches all the major components of the RAG system.

    The `@st.cache_resource` decorator ensures that these components are created only once
    per session, which significantly improves performance by avoiding re-initialization on
    every user interaction.

    Returns:
        tuple: A tuple containing the initialized doc_processor, pinecone_handler, and gemini_handler.
    """
    st.write("🚀 Initializing RAG System...")
    
    # Use a progress bar to provide visual feedback during initialization.
    progress_bar = st.progress(0)
    
    # Initialize the document processor.
    progress_bar.progress(25)
    doc_processor = DocumentProcessor(EMBEDDING_MODEL)
    
    # Initialize the Pinecone handler.
    progress_bar.progress(50)
    pinecone_handler = PineconeHandler(EMBEDDING_DIMENSIONS)
    
    # Initialize the OpenRouter handler.
    progress_bar.progress(75)
    openrouter_handler = OpenRouterHandler()
    
    progress_bar.progress(100)
    
    # Clean up the UI by removing the progress bar.
    progress_bar.empty()
    st.success("✅ All systems initialized!")
    
    return doc_processor, pinecone_handler, openrouter_handler

# ===========================
# SESSION STATE INITIALIZATION
# ===========================
# Streamlit's session state is used to persist variables across user interactions.
# This is crucial for maintaining the chat history, user session, and other stateful information.

# Initialize the chat history list if it doesn't already exist.
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Assign a unique session ID to each user session for conversation tracking.
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Keep track of documents that have already been processed to avoid redundant work.
if 'processed_docs' not in st.session_state:
    st.session_state.processed_docs = {}

# Add a key for the file uploader to allow for programmatic clearing.
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# ===========================
# MAIN UI LAYOUT
# ===========================
st.title("🔬 Research Paper AI Assistant")
st.markdown("Upload a research paper (PDF) and ask questions to get detailed, cited explanations.")
st.warning("**Tip:** This is an AI tool. Always double-check citations and factual claims against the original paper.")

col1, col2 = st.columns([2, 3])

doc_processor, pinecone_handler, openrouter_handler = initialize_system()

# --- Column 1: Document Management ---
with col1:
    st.header("📄 Document Manager")
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="Upload one or more research papers to chat with",
        key=f"uploader_{st.session_state.uploader_key}"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                file_content = uploaded_file.read()
                file_hash = hashlib.md5(file_content).hexdigest()
                uploaded_file.seek(0)
                
                if file_hash not in st.session_state.processed_docs:
                    st.info(f"🔄 Processing {uploaded_file.name}...")
                    with st.expander(f"👁️ View Processing Details: {uploaded_file.name}", expanded=True):
                        pages_data = doc_processor.extract_text_from_pdf(uploaded_file)
                        if not pages_data:
                            st.error(f"❌ Could not extract text from {uploaded_file.name}.")
                        else:
                            chunks = doc_processor.chunk_text(pages_data)
                            if not chunks:
                                st.error(f"❌ Could not create text chunks for {uploaded_file.name}.")
                            else:
                                texts = [c['text'] for c in chunks]
                                embeddings = doc_processor.create_embeddings(texts)
                                if not embeddings:
                                    st.error(f"❌ Could not create embeddings for {uploaded_file.name}.")
                                else:
                                    pinecone_handler.upsert_vectors(embeddings, chunks, uploaded_file.name)
                                    doc_sample_text = "\n".join([p['text'] for p in pages_data[:5]])
                                    doc_lang_code, doc_lang_name = detect_language_with_name(doc_sample_text)
                                    st.session_state.processed_docs[file_hash] = {
                                        'name': uploaded_file.name,
                                        'chunks': len(chunks),
                                        'processed_at': datetime.now().isoformat(),
                                        'dimensions': EMBEDDING_DIMENSIONS,
                                        'language_code': doc_lang_code,
                                        'language_name': doc_lang_name
                                    }
                                    st.success(f"✅ {uploaded_file.name} ({doc_lang_name}) processed successfully!")
                else:
                    if len(uploaded_files) == 1:
                        st.info("📋 This document has already been processed")
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                st.error("Please try uploading a different PDF file.")
    
    if st.session_state.processed_docs:
        st.subheader("📚 Processed Documents")
        for doc_hash, doc_info in st.session_state.processed_docs.items():
            with st.container():
                st.write(f"**{doc_info['name']}**")
                st.write(f"- {doc_info['chunks']} chunks created")
                if 'language_name' in doc_info:
                    st.write(f"- Language: 🌐 **{doc_info['language_name']}**")
                st.write(f"- Processed: {doc_info['processed_at'][:19]}")
                if 'dimensions' in doc_info:
                    st.write(f"- Dimensions: {doc_info['dimensions']}D")
                st.markdown("---")

    st.subheader("🧹 Memory Management")
    col_clear1, col_clear2 = st.columns(2)
    with col_clear1:
        if st.button("🗑️ Clear Chat Only", type="secondary"):
            try:
                st.session_state.messages = []
                # Note: OpenRouter handler doesn't maintain internal state, history is cleared via st.session_state
                st.success("✅ Chat history cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing chat: {str(e)}")
    with col_clear2:
        if st.button("🗑️ Clear All Memory", type="primary"):
            try:
                st.session_state.messages = []
                st.session_state.processed_docs = {}
                if 'doc_processor' in locals():
                    doc_processor.clear_cache()
                st.cache_resource.clear()
                # Increment the uploader key to force a reset of the file uploader.
                st.session_state.uploader_key += 1
                st.success("✅ All memory and caches cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing memory: {str(e)}")

# --- Column 2: Chat Interface ---
with col2:
    st.header("💬 Chat Interface")
    
    # Document Selection & Response Language Controls
    col_doc, col_lang = st.columns([3, 2])
    
    with col_doc:
        if st.session_state.processed_docs:
            st.subheader("📄 Select Document")
            doc_names = [doc_info['name'] for doc_info in st.session_state.processed_docs.values()]
            doc_options = doc_names + ["All Documents"]
            default_index = 0
            if doc_names:
                latest_doc = max(st.session_state.processed_docs.values(), key=lambda x: x['processed_at'])
                try:
                    default_index = doc_names.index(latest_doc['name'])
                except ValueError:
                    default_index = 0
            selected_doc = st.selectbox(
                "Choose document to query:",
                options=doc_options,
                index=default_index,
                help="Select a specific document or 'All Documents' to search across all uploaded files"
            )
            if selected_doc == "All Documents":
                st.session_state.selected_document = None
            else:
                st.session_state.selected_document = selected_doc
        else:
            st.subheader("📄 Document Scope")
            st.info("ℹ️ Upload a document to begin chatting.")

    with col_lang:
        st.subheader("🌐 Response Language")
        selected_response_lang = st.selectbox(
            "Choose output language:",
            options=[opt[0] for opt in LANGUAGE_OPTIONS_LIST],
            index=0,
            key="response_language_selector",
            help="Select Auto-Detect to match the document's language, or choose any preferred output language."
        )
        st.session_state.selected_response_language = selected_response_lang

    if st.session_state.processed_docs:
        active_doc_label = st.session_state.selected_document if st.session_state.get('selected_document') else "All Documents"
        st.info(f"🎯 Scope: **{active_doc_label}** | 🌐 Output: **{selected_response_lang}**")
    
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Display sources if available
                if message.get("sources"):
                    with st.expander("📚 Sources Used"):
                        for idx, src in enumerate(message["sources"]):
                            st.markdown(f"**Source {idx+1}:** `{src['source']}` (Page {src['page']})")
                            display_src_text = convert_krutidev_to_unicode(src['text'])
                            st.caption(f"> {display_src_text[:200]}...")
                
                if message["role"] == "assistant" and "language" in message:
                    st.caption(f"🌐 Language: {message['language'].upper()}")
                if "timestamp" in message:
                    st.caption(f"⏰ {message['timestamp']}")
    
    if query := st.chat_input("Ask a question about the research paper..."):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add the user's message to the chat history.
        st.session_state.messages.append({
            "role": "user",
            "content": query,
            "timestamp": timestamp
        })
        
        # Show a spinner while processing the query.
        with st.spinner("🤔 Processing your question..."):
            try:
                # First, check if any documents have been uploaded.
                if not st.session_state.processed_docs:
                    response = "Please upload a research paper first before asking a question."
                    language = 'en'
                else:
                    # 1. Create an embedding for the user's query.
                    query_embeddings = doc_processor.create_embeddings([query])
                    if not query_embeddings:
                        response = "I could not process your question. Please try rephrasing it."
                        language = 'en'
                    else:
                        query_embedding = query_embeddings[0]
                        
                        # 2. Retrieve the most relevant document chunks from Pinecone.
                        filter_doc_name = getattr(st.session_state, 'selected_document', None)
                        results = pinecone_handler.query_vectors(query_vector=query_embedding, top_k=5, filter_source=filter_doc_name)
                        
                        # 3. Extract the text content from the search results to form the context.
                        context_clauses = []
                        sources_used = []
                        if results.matches:
                            for match in results.matches:
                                if match.metadata and 'text' in match.metadata:
                                    source_name = match.metadata.get('source', 'Unknown Document')
                                    page_num = match.metadata.get('page', 'Unknown Page')
                                    text_content = match.metadata['text']
                                    
                                    clause = f"--- Source: [{source_name}, Page {page_num}] ---\n{text_content}"
                                    context_clauses.append(clause)
                                    sources_used.append({"source": source_name, "page": page_num, "text": text_content})
                        
                        # If no relevant clauses are found, inform the user.
                        if not context_clauses:
                            response = "I couldn't find any relevant clauses in the document to answer your question."
                            language = 'en'
                        else:
                            # 4. Determine document language and target response language
                            selected_doc_info = None
                            if filter_doc_name and filter_doc_name != "All Documents":
                                for d in st.session_state.processed_docs.values():
                                    if d.get('name') == filter_doc_name:
                                        selected_doc_info = d
                                        break
                            
                            if selected_doc_info and selected_doc_info.get('language_code'):
                                doc_lang_code = selected_doc_info['language_code']
                                doc_lang_name = selected_doc_info.get('language_name', doc_lang_code)
                            else:
                                raw_context_text = "\n".join([s.get('text', '') for s in sources_used])
                                doc_lang_code, doc_lang_name = detect_language_with_name(raw_context_text)
                            
                            chosen_pref = st.session_state.get("response_language_selector", "🌐 Auto-Detect (Match PDF Language)")
                            target_lang_code, target_lang_name, is_explicit_override = resolve_target_language(
                                chosen_pref, doc_lang_code, doc_lang_name
                            )
                            language = target_lang_code

                            # 5. Construct the final prompt for the LLM model.
                            context = "\n\n".join(context_clauses)
                            
                            if is_explicit_override:
                                lang_instruction = f"""CRITICAL LANGUAGE RULE:
The user has explicitly selected {target_lang_name} ({target_lang_code}) as their desired response language.
You MUST write your entire response, explanations, quotes analysis, and summaries in {target_lang_name}.
Even though the source document is in {doc_lang_name} and the user question may be in another language, formulate your entire response in {target_lang_name}."""
                            else:
                                lang_instruction = f"""CRITICAL LANGUAGE RULE:
The uploaded source document is in {doc_lang_name} (language code: {doc_lang_code}).
You MUST write your entire response, explanations, quotes, and summaries in the SAME LANGUAGE as the source document ({doc_lang_name}).
Even if the user asks their question in English or any other language, formulate your entire response in {doc_lang_name}."""

                            system_prompt = f"""You are an Expert Research Paper & Legal AI Assistant. Your task is to explain and answer questions about academic, scientific, and legal documents with precision and clarity.

{lang_instruction}

Guidelines:
1. Use ONLY the facts and context from the uploaded document provided below. Do NOT make up facts.
2. Provide clear, structured explanations of concepts and findings in {target_lang_name}.
3. When explaining concepts:
   - Quote or reference the original text.
   - Paraphrase and explain complex terminology simply in {target_lang_name}.
4. ALWAYS cite the exact source and page number when stating a fact, using the format `[Paper Name, Page X]` based on the Source metadata in the context.
5. If the document context does not contain the answer, state that it is not mentioned in the paper (in {target_lang_name}).
6. Be concise, structured, and comprehensive.
"""
                            
                            # Combine the system prompt, context, and user query into a single prompt.
                            prompt = f"""{system_prompt}

DOCUMENT CONTEXT:
```
{context}
```

SOURCE DOCUMENT LANGUAGE: {doc_lang_name} ({doc_lang_code})
TARGET RESPONSE LANGUAGE: {target_lang_name} ({target_lang_code})
USER QUESTION: "{query}"

INSTRUCTION: Please answer the user's question based strictly on the document context above. Your entire response MUST be written in {target_lang_name}, following all guidelines and citations.
"""
                            
                            # 6. Generate the response using the OpenRouter handler.
                            response = openrouter_handler.get_response(prompt, st.session_state.messages[:-1])
            except Exception as e:
                # Gracefully handle any exceptions that occur during query processing.
                import traceback
                error_details = traceback.format_exc()
                st.error(f"❌ Error processing query: {str(e)}")
                st.error(f"📋 Error details: {error_details}")
                response = f"Sorry, I encountered an error while processing your question: {str(e)}"
                language = 'en'
        
        # --- Display Assistant Response ---
        # Add the assistant's response to the chat history.
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "language": language,
            "timestamp": timestamp,
            "sources": sources_used if 'sources_used' in locals() else []
        })
        
        # Rerun to refresh the chat display with the new message
        st.rerun()

# ===========================
# SIDEBAR INFORMATION
# ===========================
# The sidebar provides additional information and functionality.
with st.sidebar:
    st.header("📊 System Information")
    
    # Display key metrics about the current session.
    st.metric("Messages in Chat", len(st.session_state.messages))
    st.metric("Documents Processed", len(st.session_state.processed_docs))
    st.metric("Session ID", st.session_state.session_id[:8] + "...")

    # --- Supported Languages ---
    st.header("🌐 Supported Languages")
    st.markdown("""
    The AI can understand and respond in the following languages:
    - **English**
    - **Indian Languages:** Bengali, Hindi, Kannada, Malayalam, Tamil, Telugu
    - **Other Languages:** Chinese, French, German, Italian, Japanese, Portuguese, Spanish
    """)
    
    # --- Export Functionality ---
    st.header("💾 Export Options")
    # Button to export the current conversation to a JSON file.
    if st.button("📥 Export Conversation"):
        export_data = {
            'session_id': st.session_state.session_id,
            'messages': st.session_state.messages,
            'processed_docs': st.session_state.processed_docs,
            'configuration': {
                'embedding_model': EMBEDDING_MODEL,
                'dimensions': EMBEDDING_DIMENSIONS
            },
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Convert the export data to a JSON string.
        json_data = json.dumps(export_data, indent=2)
        
        # Create a download button for the JSON data.
        st.download_button(
            label="💾 Download JSON",
            data=json_data,
            file_name=f"rag_conversation_{st.session_state.session_id[:8]}.json",
            mime="application/json"
        )
    
    # --- Configuration Guide ---
    # An expander to guide users on how to change the embedding model configuration.
    st.header("⚙️ Configuration Guide")
    with st.expander("📋 How to Change Embedding Model", expanded=False):
        st.markdown("""
        **To change the embedding model:**
        
        1. **Edit the configuration section** at the top of the script.
        2. **Comment out the active model** (Option 1 by default).
        3. **Uncomment your desired model** (e.g., Option 2 for English-only focus).
        
        **Example: Switching to the English-only model:**
        ```python
        # Option 1: 384-dimensional multilingual embeddings (Recommended for broad language support).
        # EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
        # EMBEDDING_DIMENSIONS = 384

        # Option 2: 384-dimensional English-focused embeddings (Faster, for English-only documents).
        EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
        EMBEDDING_DIMENSIONS = 384
        ```
        
        4. **Clear All Memory** using the button in the sidebar and restart the app.
        """)
    
    # --- Model Comparison ---
    # A brief comparison of the available embedding models.
    st.header("🔍 Model Comparison")
    st.markdown("""
    **Multilingual Model (Default):**
    - `paraphrase-multilingual-MiniLM-L12-v2` (384D)
    - **Best for:** Supporting a wide range of languages, including the ones listed in the prompt.
    
    **English-focused Models:**
    - `all-MiniLM-L6-v2` (384D): Fast, good quality for English.
    - `all-mpnet-base-v2` (768D): Higher quality for English, but larger and slower.
    """)
    
    # --- Help Section ---
    # An expander with step-by-step instructions on how to use the application.
    st.header("❓ Help & Instructions")
    with st.expander("📖 How to Use", expanded=True):
        st.markdown("""
        **Step 1:** Upload a research paper (PDF) using the file uploader.
        
        **Step 2:** Wait for the document to be processed.
        
        **Step 3:** Use the dropdown to select the document you want to ask questions about.
        
        **Step 4:** Ask questions in the chat input, such as 'Summarize this document' or 'Explain the termination clause.'
        
        **Step 5:** The AI will provide a plain-language explanation based on the document's content.
        
        **Step 6:** Use the 'Clear' buttons to manage your session.
        """)
    
    
    # --- Sample Questions ---
    # A section to provide users with examples of questions they can ask.
    st.header("💡 Sample Questions")
    st.write("Try asking questions like:")
    
    sample_queries = [
        "Can you summarize the main findings of this paper?",
        "What methodology was used in this study?",
        "What are the limitations mentioned by the authors?",
        "Explain the conclusion in simple terms."
    ]
    
    # Display the sample questions as buttons.
    for i, query in enumerate(sample_queries):
        if st.button(query, key=f"sample_query_{i}"):
            # Add the sample query to messages and process it
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({
                "role": "user",
                "content": query,
                "timestamp": timestamp
            })
            
            # Process the sample query
            with st.spinner("🤔 Processing your question..."):
                try:
                    # First, check if any documents have been uploaded.
                    if not st.session_state.processed_docs:
                        response = "Please upload a research paper first before asking a question."
                        language = 'en'
                    else:
                        # 1. Create an embedding for the sample query.
                        query_embeddings = doc_processor.create_embeddings([query])
                        if not query_embeddings:
                            response = "I could not process your question. Please try rephrasing it."
                            language = 'en'
                        else:
                            query_embedding = query_embeddings[0]
                            
                            # 2. Retrieve the most relevant document chunks from Pinecone.
                            filter_doc_name = getattr(st.session_state, 'selected_document', None)
                            results = pinecone_handler.query_vectors(query_vector=query_embedding, top_k=5, filter_source=filter_doc_name)
                            
                            # 3. Extract the text content from the search results to form the context.
                            context_clauses = []
                            sources_used = []
                            if results.matches:
                                for match in results.matches:
                                    if match.metadata and 'text' in match.metadata:
                                        source_name = match.metadata.get('source', 'Unknown Document')
                                        page_num = match.metadata.get('page', 'Unknown Page')
                                        text_content = match.metadata['text']
                                        
                                        clause = f"--- Source: [{source_name}, Page {page_num}] ---\n{text_content}"
                                        context_clauses.append(clause)
                                        sources_used.append({"source": source_name, "page": page_num, "text": text_content})
                            
                            # If no relevant clauses are found, inform the user.
                            if not context_clauses:
                                response = "I couldn't find any relevant clauses in the document to answer your question."
                                language = 'en'
                            else:
                                # 4. Determine document language and target response language
                                selected_doc_info = None
                                if filter_doc_name and filter_doc_name != "All Documents":
                                    for d in st.session_state.processed_docs.values():
                                        if d.get('name') == filter_doc_name:
                                            selected_doc_info = d
                                            break
                                
                                if selected_doc_info and selected_doc_info.get('language_code'):
                                    doc_lang_code = selected_doc_info['language_code']
                                    doc_lang_name = selected_doc_info.get('language_name', doc_lang_code)
                                else:
                                    raw_context_text = "\n".join([s.get('text', '') for s in sources_used])
                                    doc_lang_code, doc_lang_name = detect_language_with_name(raw_context_text)
                                
                                chosen_pref = st.session_state.get("response_language_selector", "🌐 Auto-Detect (Match PDF Language)")
                                target_lang_code, target_lang_name, is_explicit_override = resolve_target_language(
                                    chosen_pref, doc_lang_code, doc_lang_name
                                )
                                language = target_lang_code

                                # 5. Construct the final prompt for the LLM model.
                                context = "\n\n".join(context_clauses)
                                
                                if is_explicit_override:
                                    lang_instruction = f"""CRITICAL LANGUAGE RULE:
The user has explicitly selected {target_lang_name} ({target_lang_code}) as their desired response language.
You MUST write your entire response, explanations, quotes analysis, and summaries in {target_lang_name}.
Even though the source document is in {doc_lang_name} and the user question may be in another language, formulate your entire response in {target_lang_name}."""
                                else:
                                    lang_instruction = f"""CRITICAL LANGUAGE RULE:
The uploaded source document is in {doc_lang_name} (language code: {doc_lang_code}).
You MUST write your entire response, explanations, quotes, and summaries in the SAME LANGUAGE as the source document ({doc_lang_name}).
Even if the user asks their question in English or any other language, formulate your entire response in {doc_lang_name}."""

                                system_prompt = f"""You are an Expert Research Paper & Legal AI Assistant. Your task is to explain and answer questions about academic, scientific, and legal documents with precision and clarity.

{lang_instruction}

Guidelines:
1. Use ONLY the facts and context from the uploaded document provided below. Do NOT make up facts.
2. Provide clear, structured explanations of concepts and findings in {target_lang_name}.
3. When explaining concepts:
   - Quote or reference the original text.
   - Paraphrase and explain complex terminology simply in {target_lang_name}.
4. ALWAYS cite the exact source and page number when stating a fact, using the format `[Paper Name, Page X]` based on the Source metadata in the context.
5. If the document context does not contain the answer, state that it is not mentioned in the paper (in {target_lang_name}).
6. Be concise, structured, and comprehensive.
"""
                                
                                # Combine the system prompt, context, and user query into a single prompt.
                                prompt = f"""{system_prompt}

DOCUMENT CONTEXT:
```
{context}
```

SOURCE DOCUMENT LANGUAGE: {doc_lang_name} ({doc_lang_code})
TARGET RESPONSE LANGUAGE: {target_lang_name} ({target_lang_code})
USER QUESTION: "{query}"

INSTRUCTION: Please answer the user's question based strictly on the document context above. Your entire response MUST be written in {target_lang_name}, following all guidelines and citations.
"""
                                
                                # 6. Generate the response using the OpenRouter handler.
                                response = openrouter_handler.get_response(prompt, st.session_state.messages[:-1])
                except Exception as e:
                    # Gracefully handle any exceptions that occur during query processing.
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"❌ Error processing query: {str(e)}")
                    st.error(f"📋 Error details: {error_details}")
                    response = f"Sorry, I encountered an error while processing your question: {str(e)}"
                    language = 'en'
            
            # Add the assistant's response to the chat history.
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "language": language,
                "timestamp": timestamp,
                "sources": sources_used if 'sources_used' in locals() else []
            })
            
            # Rerun to update the UI
            st.rerun()
    
    # --- Features & Technical Details ---
    st.header("🔧 Features & Technical Details")
    with st.expander("⚙️ View System Components", expanded=False):
        st.markdown(f"""
        - **PDF Processing**: Extracts text from uploaded PDFs completely locally using PyMuPDF.
        - **Multilingual Embeddings**: Uses the `{EMBEDDING_MODEL}` model to create vector embeddings that support multiple languages.
        - **Vector Search**: Stores and searches document embeddings using the Pinecone vector database ({EMBEDDING_DIMENSIONS} dimensions).
        - **AI-Powered Answers**: Leverages OpenRouter AI models to generate responses based on the retrieved document context.
        - **Chat Interface**: Provides a real-time chat experience built with Streamlit.
        - **Conversation Memory**: Remembers the context of the current conversation.
        """)

# ===========================
# FOOTER
# ===========================
# A simple footer for the application.
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit, OpenRouter, and Pinecone</p>
    <p>Research Paper AI Assistant</p>
</div>
""", unsafe_allow_html=True)
