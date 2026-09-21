# ============================================================
# EXP-2: RAG-BASED QUESTION ANSWERING SYSTEM
# Implement indexing, retrieval, and response generation
# ============================================================

import re
import math
from collections import Counter
from groq import Groq


# ============================================================
# 1. GROQ CONFIGURATION
# ============================================================

# Put your NEW Groq API key here
GROQ_API_KEY = "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"

MODEL = "openai/gpt-oss-120b"

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# 2. SAMPLE KNOWLEDGE BASE
# ============================================================

documents = [
    """
    Cybersecurity is the practice of protecting computers, networks,
    applications, devices, and data from unauthorized access,
    attacks, damage, or disruption. It includes areas such as
    network security, endpoint security, identity and access
    management, application security, and data security.
    """,

    """
    A Security Operations Center, commonly called a SOC, monitors
    an organization's security environment. SOC analysts investigate
    security alerts, identify suspicious activity, analyze logs,
    respond to incidents, and help prevent future attacks.
    """,

    """
    Phishing is a social engineering attack in which attackers try
    to trick users into revealing sensitive information such as
    passwords, banking information, or authentication codes.
    Phishing commonly occurs through email, text messages,
    malicious websites, and fake login pages.
    """,

    """
    Multi-factor authentication, or MFA, provides an additional
    layer of security during login. Instead of relying only on a
    password, MFA can require another factor such as an authenticator
    application, security key, fingerprint, or one-time password.
    """,

    """
    A firewall is a security system that monitors and controls
    network traffic based on predefined security rules. Firewalls
    can allow legitimate traffic and block unauthorized connections.
    They can be implemented as hardware, software, or cloud-based
    security controls.
    """,

    """
    SIEM stands for Security Information and Event Management.
    A SIEM platform collects and analyzes security logs from
    different systems such as servers, endpoints, applications,
    firewalls, and network devices. SIEM helps security teams
    detect suspicious activities and investigate incidents.
    """
]


# ============================================================
# 3. TEXT PREPROCESSING
# ============================================================

def preprocess(text):

    text = text.lower()

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text)

    return words


# ============================================================
# 4. DOCUMENT INDEXING
# ============================================================

def create_index(documents):

    index = []

    for document in documents:

        words = preprocess(document)

        word_count = Counter(words)

        index.append({
            "text": document.strip(),
            "words": word_count
        })

    return index


# ============================================================
# 5. COSINE SIMILARITY
# ============================================================

def cosine_similarity(query_words, document_words):

    all_words = set(query_words.keys()) | set(document_words.keys())

    if not all_words:
        return 0

    query_vector = []
    document_vector = []

    for word in all_words:

        query_vector.append(query_words[word])

        document_vector.append(document_words[word])

    dot_product = sum(
        q * d
        for q, d in zip(query_vector, document_vector)
    )

    query_magnitude = math.sqrt(
        sum(q * q for q in query_vector)
    )

    document_magnitude = math.sqrt(
        sum(d * d for d in document_vector)
    )

    if query_magnitude == 0 or document_magnitude == 0:
        return 0

    return dot_product / (
        query_magnitude * document_magnitude
    )


# ============================================================
# 6. RETRIEVAL
# ============================================================

def retrieve_documents(query, index, top_k=3):

    query_words = Counter(
        preprocess(query)
    )

    results = []

    for document in index:

        score = cosine_similarity(
            query_words,
            document["words"]
        )

        results.append(
            (score, document["text"])
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# 7. GROQ RESPONSE GENERATION
# ============================================================

def generate_answer(question, retrieved_documents):

    context = "\n\n".join(
        document
        for score, document in retrieved_documents
        if score > 0
    )

    if not context:

        return "I could not find relevant information in the knowledge base."

    prompt = f"""
You are a helpful cybersecurity assistant.

Answer the user's question using ONLY the information
provided in the context.

CONTEXT:
{context}

USER QUESTION:
{question}

RULES:
1. Use only the provided context.
2. Do not invent information.
3. If the answer is not present in the context,
   clearly say that the information is not available.
4. Give a simple and clear answer.
5. Do not mention the internal RAG process.
"""

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content.strip()

    except Exception as e:

        print("\nGroq API Error:")
        print(e)

        return None


# ============================================================
# 8. MAIN RAG WORKFLOW
# ============================================================

def rag_question_answering():

    print("\n")
    print("=" * 65)
    print("EXP-2: RAG-BASED QUESTION ANSWERING SYSTEM")
    print("=" * 65)

    # --------------------------------------------------------
    # STEP 1: INDEXING
    # --------------------------------------------------------

    print("\n[1/3] Indexing knowledge base...")

    index = create_index(documents)

    print(
        "Indexed documents:",
        len(index)
    )

    # --------------------------------------------------------
    # USER QUESTION
    # --------------------------------------------------------

    question = input(
        "\nAsk a question: "
    ).strip()

    if not question:

        print("\nQuestion cannot be empty.")

        return

    # --------------------------------------------------------
    # STEP 2: RETRIEVAL
    # --------------------------------------------------------

    print("\n[2/3] Retrieving relevant documents...")

    retrieved_documents = retrieve_documents(
        question,
        index,
        top_k=3
    )

    print("\nRETRIEVED DOCUMENTS")
    print("-" * 65)

    for number, (score, document) in enumerate(
        retrieved_documents,
        start=1
    ):

        print(
            f"\nDocument {number}"
        )

        print(
            f"Similarity Score: {score:.4f}"
        )

        print(document)

    # --------------------------------------------------------
    # STEP 3: RESPONSE GENERATION
    # --------------------------------------------------------

    print("\n[3/3] Generating answer...")

    answer = generate_answer(
        question,
        retrieved_documents
    )

    if answer:

        print("\nFINAL ANSWER")
        print("=" * 65)

        print(answer)


# ============================================================
# 9. PROGRAM START
# ============================================================

if __name__ == "__main__":

    if (
        not GROQ_API_KEY
        or
        GROQ_API_KEY == "PASTE_YOUR_GROQ_API_KEY_HERE"
    ):

        print("\nERROR")
        print("-" * 65)

        print(
            "Please add your NEW Groq API key "
            "at the top of lab-2.py."
        )

    else:

        rag_question_answering()