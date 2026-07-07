"""Embedding + retrieval.
Embeds chunks with all-MiniLM-L6-v2, stores in ChromaDB, retrieves top-k.
"""
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import make_chunks

COLLECTION_NAME = "csi_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

def build_store():
    """Embed all chunks and store in ChromaDB."""
    chunks, metadatas = make_chunks()
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(chunks, show_progress_bar=True).tolist()
    client = chromadb.Client()
    # delete collection if it already exists
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    collection = client.create_collection(COLLECTION_NAME)
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Stored {len(chunks)} chunks in ChromaDB")
    return client, collection, model

def retrieve(query, collection, model, k=TOP_K):
    """Return top-k chunks for a query with distances."""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )
    return results

if __name__ == "__main__":
    client, collection, model = build_store()

    test_queries = [
        "Does Professor Shuqun Zhang help students during labs?",
        "What do students say about Professor Chen's exams?",
        "Is Professor Ali Mohamed a good teacher?",
    ]

    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {q}")
        print(f"{'='*60}")
        results = retrieve(q, collection, model)
        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            dist = results["distances"][0][i]
            source = results["metadatas"][0][i]["source"]
            print(f"\n  [{i+1}] (distance: {dist:.3f}) [{source}]")
            print(f"  {doc[:200]}...")