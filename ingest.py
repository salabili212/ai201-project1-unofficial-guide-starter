"""Ingestion + chunking pipeline (v2).
One review = one chunk. Professor name derived from filename,
so files don't need header lines. Splits on line breaks.
"""
import os
import re

DOCS_DIR = "documents"

# filename -> professor name
NAMES = {
    "rmp_alnajjar.txt": "Professor Fuad Alnajjar",
    "rmp_cappellari.txt": "Professor Paolo Cappellari",
    "rmp_chen.txt": "Professor Cong Chen",
    "rmp_deredita.txt": "Professor Michael D'eredita",
    "rmp_mohamed.txt": "Professor Ali Mohamed",
    "rmp_petingi.txt": "Professor Louis Petingi",
    "rmp_rao.txt": "Professor Jun Rao",
    "rmp_wang.txt": "Professor Zhiqi Wang",
    "rmp_zelikovitz.txt": "Professor Sarah Zelikovitz",
    "rmp_zhang_shuqun.txt": "Professor Shuqun Zhang",
    "rmp_zhang_xiaowen.txt": "Professor Xiaowen (Sean) Zhang",
}

def split_reviews(text):
    """Each non-empty line = one review. Strips leading '1-' style numbering."""
    reviews = []
    for line in text.split("\n"):
        line = line.strip()
        line = re.sub(r"^\d+\s*[-.)_]\s*", "", line)   # remove "1-", "2." etc.
        # skip header lines like "Professor X - Computer Science - ..."
        if line.lower().startswith("professor ") and " - " in line:
            continue
        if len(line) >= 30:                            # skip junk/fragments
            reviews.append(line)
    return reviews

def make_chunks():
    chunks, metadatas = [], []
    for fname in sorted(os.listdir(DOCS_DIR)):
        if not fname.endswith(".txt"):
            continue
        prof = NAMES.get(fname)
        if prof is None:
            print(f"WARNING: {fname} not in NAMES map — skipped. Add it!")
            continue
        with open(os.path.join(DOCS_DIR, fname), encoding="utf-8", errors="replace") as f:
            text = f.read()
        for i, review in enumerate(split_reviews(text)):
            chunks.append(f"{prof}: {review}")
            metadatas.append({"source": fname, "position": i})
    return chunks, metadatas

if __name__ == "__main__":
    chunks, metas = make_chunks()
    sources = sorted(set(m["source"] for m in metas))
    print(f"Loaded {len(sources)} documents")
    for s in sources:
        n = sum(1 for m in metas if m["source"] == s)
        print(f"  {s}: {n} chunks")
    print(f"Total chunks: {len(chunks)}\n")
    print("=== 5 SAMPLE CHUNKS ===")
    import random
    for idx in random.sample(range(len(chunks)), min(5, len(chunks))):
        print(f"\n--- Chunk {idx} (source: {metas[idx]['source']}) ---")
        print(chunks[idx])