"""Query pipeline: retrieve chunks + generate grounded answer via Groq."""
import os
from dotenv import load_dotenv
from groq import Groq
from embed import build_store, retrieve

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about 
Computer Science professors at the College of Staten Island, based ONLY on 
student reviews provided below. 

Rules:
1. Answer ONLY from the provided reviews. Do NOT use outside knowledge.
2. Cite which professor and source file each piece of information comes from.
3. If the reviews do not contain enough information to answer, say exactly: 
   "I don't have enough information to answer that based on the available reviews."
4. Represent the range of student opinions — don't cherry-pick only positive or negative.
"""

def ask(question, collection, model):
    """Retrieve relevant chunks and generate a grounded answer."""
    results = retrieve(question, collection, model)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    
    # build context from retrieved chunks
    context = ""
    sources = []
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        context += f"\n[Review {i+1}] (from {meta['source']}): {doc}\n"
        if meta["source"] not in sources:
            sources.append(meta["source"])
    
    user_prompt = f"""Based on the following student reviews, answer this question:

Question: {question}

Reviews:
{context}

Remember: answer ONLY from these reviews. Cite sources."""

    response = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    
    answer = response.choices[0].message.content
    return {"answer": answer, "sources": sources}