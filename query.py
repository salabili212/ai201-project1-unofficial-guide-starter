"""Query pipeline: retrieve chunks + generate a grounded answer.

Generation runs through generator.py, which uses the Groq API when a key is
configured and a small local model otherwise. Both backends get the same
prompt and the same retrieved context.
"""
from dotenv import load_dotenv

from embed import retrieve
from generator import generate

load_dotenv()

# Cosine distances above this are treated as "nothing relevant was found".
# Chosen from observed runs: on-topic chunks land at 0.48-0.85, while the
# out-of-scope parking query returned its best match at 1.404. Anything past
# ~1.1 is a chunk that shares vocabulary with the query but not subject matter.
RELEVANCE_THRESHOLD = 1.1

REFUSAL = (
    "I don't have enough information to answer that based on the available reviews."
)


def ask(question, collection, model):
    """Retrieve relevant chunks and generate a grounded answer.

    Returns a dict with:
        answer   — the generated response, or the refusal string
        sources  — source filenames of the chunks actually used
        backend  — which generation backend produced the answer
        distances — distance score of each retrieved chunk, for transparency
    """
    results = retrieve(question, collection, model)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    # Keep only chunks close enough to plausibly be about the question. This
    # makes refusal a property of the pipeline rather than something we hope
    # the language model chooses to do. It also stops a thinly-covered
    # professor's answer from being padded with reviews of other professors
    # just because top-k is a fixed number.
    kept = [
        (doc, meta, dist)
        for doc, meta, dist in zip(docs, metas, dists)
        if dist <= RELEVANCE_THRESHOLD
    ]

    if not kept:
        return {
            "answer": REFUSAL,
            "sources": [],
            "backend": "none (no chunk within relevance threshold)",
            "distances": [round(d, 3) for d in dists],
        }

    context = ""
    sources = []
    for i, (doc, meta, dist) in enumerate(kept, start=1):
        context += f"\n[Review {i}] (from {meta['source']}): {doc}\n"
        if meta["source"] not in sources:
            sources.append(meta["source"])

    user_prompt = f"""Based on the following student reviews, answer this question:

Question: {question}

Reviews:
{context}

Remember: answer ONLY from these reviews. Cite sources."""

    answer, backend = generate(user_prompt)

    return {
        "answer": answer,
        "sources": sources,
        "backend": backend,
        "distances": [round(dist, 3) for _, _, dist in kept],
    }
