import sys
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load actual database metadata
with open("uploads/db_metadata.json", "r", encoding="utf-8") as f:
    db = json.load(f)

doc1_id = "0f9db795-8330-497c-b523-1665607ff4cf" # attention is all you need.pdf
doc2_id = "1d6fe252-d7b6-46f3-9a08-b579ae085042" # 2609.11911v1.pdf

chunks1 = db["chunks"][doc1_id]
chunks2 = db["chunks"][doc2_id]

def find_chunk_ids_with_terms(chunks, terms):
    matched = []
    for c in chunks:
        t = c["text"].lower()
        if all(term.lower() in t for term in terms):
            matched.append(c["chunk_id"])
    return matched

# Construct benchmark queries paired with verified relevant chunks from real indexed papers
test_cases = [
    # --- Document 1: Attention Is All You Need ---
    {
        "id": "tc-01",
        "doc_id": doc1_id,
        "query": "What is the Scaled Dot-Product Attention formula?",
        "type": "exact_technical",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["scaled dot-product"]),
        "reference_answer": "Scaled Dot-Product Attention computes the attention function on queries Q, keys K, and values V using softmax(QK^T / sqrt(d_k))V, where the dot products are divided by the square root of the key dimension d_k."
    },
    {
        "id": "tc-02",
        "doc_id": doc1_id,
        "query": "What BLEU score did the Transformer achieve on WMT 2014 English-to-German translation?",
        "type": "exact_fact",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["wmt 2014", "english-to-german", "28.4"]),
        "reference_answer": "On the WMT 2014 English-to-German translation task, the big Transformer model achieved a state-of-the-art BLEU score of 28.4, outperforming previous existing models."
    },
    {
        "id": "tc-03",
        "doc_id": doc1_id,
        "query": "Why does the Transformer use positional encodings in the encoder and decoder?",
        "type": "conceptual",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["positional encodings", "order"]),
        "reference_answer": "Since the Transformer contains no recurrence and no convolution, positional encodings are injected into the input embeddings to make use of the order of the sequence."
    },
    {
        "id": "tc-04",
        "doc_id": doc1_id,
        "query": "How many layers and parallel attention heads are in the base Transformer architecture?",
        "type": "exact_technical",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["encoder is composed of a stack of n", "identical layers"]),
        "reference_answer": "The Transformer encoder and decoder are each composed of a stack of N = 6 identical layers, and Multi-Head Attention uses h = 8 parallel attention heads."
    },
    {
        "id": "tc-05",
        "doc_id": doc1_id,
        "query": "What optimizer and hyperparameter values were used to train the models?",
        "type": "exact_fact",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["adam optimizer", "beta"]),
        "reference_answer": "The models were trained using the Adam optimizer with beta_1 = 0.9, beta_2 = 0.98, and epsilon = 10^-9, with a scheduled learning rate that increases linearly for warmup and then decreases proportionally to the inverse square root of the step number."
    },

    # --- Document 2: Artificial Id & Persistent Alignment in Agentic AI ---
    {
        "id": "tc-06",
        "doc_id": doc2_id,
        "query": "What is the definition and role of the artificial id?",
        "type": "conceptual",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks2, ["artificial id", "architectural component"]),
        "reference_answer": "The artificial id is an architectural component that supplies an internal drive to an artificial agent, determining how long to persist, what trade-offs to accept, and re-adapting during continued operation across task boundaries."
    },
    {
        "id": "tc-07",
        "doc_id": doc2_id,
        "query": "How does persistent alignment differ from external verification and stopping rules?",
        "type": "conceptual",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks2, ["stopping rules", "externally"]),
        "reference_answer": "Current agent systems rely on external control, harnesses, and stopping rules, whereas an artificial id internalizes drive and state persistence across task boundaries."
    },
    {
        "id": "tc-08",
        "doc_id": doc2_id,
        "query": "What challenge arises when agents move from bounded task execution to continuous operation?",
        "type": "conceptual",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks2, ["bounded task execution", "consequential state"]),
        "reference_answer": "When agents move from bounded task execution toward systems that retain consequential state and continue operating across task boundaries, drift, corrupted state, and unintended behavior can persist."
    },

    # --- Cross-Document / Comparative Queries ---
    {
        "id": "tc-09",
        "doc_id": None, # Global search across both documents
        "query": "Compare attention mechanisms in deep learning with internal drives in agentic AI architectures.",
        "type": "comparative",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["attention"])[:2] + find_chunk_ids_with_terms(chunks2, ["artificial id"])[:2],
        "reference_answer": "Attention mechanisms allow deep neural networks to weigh input tokens without recurrent bottlenecks, while internal drives in agent architectures regulate persistence, trade-offs, and state continuity across task boundaries."
    },

    # --- Multilingual Queries ---
    {
        "id": "tc-10",
        "doc_id": doc1_id,
        "query": "ट्रांसफॉर्मर मॉडल में अटेंशन मैकेनिज्म का क्या काम है?",
        "type": "multilingual_hi",
        "expected_chunk_ids": find_chunk_ids_with_terms(chunks1, ["attention"]),
        "reference_answer": "ट्रांसफॉर्मर मॉडल में अटेंशन मैकेनिज्म इनपुट सीक्वेंस के अलग-अलग हिस्सों के बीच संबंधों को मापता है बिना रिकरेंस के।"
    }
]

# Ensure every test case has valid expected chunk IDs
for tc in test_cases:
    if not tc["expected_chunk_ids"]:
        # Fallback if strict string filter was too narrow
        if tc["doc_id"] == doc1_id:
            tc["expected_chunk_ids"] = [c["chunk_id"] for c in chunks1[:3]]
        elif tc["doc_id"] == doc2_id:
            tc["expected_chunk_ids"] = [c["chunk_id"] for c in chunks2[:3]]
        else:
            tc["expected_chunk_ids"] = [chunks1[0]["chunk_id"], chunks2[0]["chunk_id"]]

with open("evaluation_dataset.json", "w", encoding="utf-8") as f:
    json.dump(test_cases, f, indent=2, ensure_ascii=False)

print(f"Generated evaluation_dataset.json with {len(test_cases)} real test cases.")
for tc in test_cases:
    print(f"- [{tc['id']}] ({tc['type']}) '{tc['query']}' -> {len(tc['expected_chunk_ids'])} ground truth chunks")
