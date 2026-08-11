"""Evaluation harness for The Unofficial Guide.

Runs the five evaluation questions from planning.md end to end, plus a
diagnostic probe for the ambiguous-name failure case, and writes everything
to eval_output.md: the retrieved chunks with their distance scores, the
generated answer, and the sources cited.

Run once with:  python evaluate.py
"""
import traceback

from embed import build_store, retrieve, TOP_K
from query import ask

EVAL_QUESTIONS = [
    (1, "Does Professor Shuqun Zhang help students during labs?"),
    (2, "Do students think Professor Fuad Alnajjar's positive reviews are trustworthy?"),
    (3, "Does Professor Shuqun Zhang give practice exams?"),
    (4, "What do students say about Professor Paolo Cappellari's homework load and flexibility?"),
    (5, "Where can I park near the CS building at CSI?"),
]

# Not part of the graded five - this probes the ambiguity named as a risk in
# planning.md, so the failure case can be described from real output.
DIAGNOSTIC_QUESTIONS = [
    ("Ambiguous surname probe", "Is Professor Zhang a good teacher?"),
]


def dump_retrieval(f, question, collection, model):
    """Write the retrieved chunks and distances for one question."""
    results = retrieve(question, collection, model)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    f.write(f"**Retrieved chunks (top-{TOP_K}):**\n\n")
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
        f.write(f"{i}. `{meta['source']}` (distance {dist:.3f})\n")
        f.write(f"   > {doc}\n\n")
    return sorted({m["source"] for m in metas})


def main():
    print("Building vector store...")
    client, collection, model = build_store()
    print("Store ready. Running evaluation...\n")

    with open("eval_output.md", "w", encoding="utf-8") as f:
        f.write("# Evaluation run output\n\n")
        f.write("Raw output from `python evaluate.py`. Retrieved chunks, distance ")
        f.write("scores, generated answers, and cited sources for each question.\n\n")

        f.write("## Evaluation questions\n\n")
        for num, question in EVAL_QUESTIONS:
            print(f"[{num}/5] {question}")
            f.write(f"### Q{num}. {question}\n\n")
            try:
                sources = dump_retrieval(f, question, collection, model)
                result = ask(question, collection, model)
                f.write("**Generated answer:**\n\n")
                f.write("```\n" + result["answer"].strip() + "\n```\n\n")
                f.write(f"**Sources returned:** {', '.join(result['sources'])}\n\n")
            except Exception:
                f.write("**ERROR:**\n\n```\n" + traceback.format_exc() + "\n```\n\n")
                print("  ERROR - see eval_output.md")
            f.write("---\n\n")

        f.write("## Diagnostic probes (not graded questions)\n\n")
        for label, question in DIAGNOSTIC_QUESTIONS:
            print(f"[probe] {question}")
            f.write(f"### {label}: {question}\n\n")
            try:
                dump_retrieval(f, question, collection, model)
                result = ask(question, collection, model)
                f.write("**Generated answer:**\n\n")
                f.write("```\n" + result["answer"].strip() + "\n```\n\n")
                f.write(f"**Sources returned:** {', '.join(result['sources'])}\n\n")
            except Exception:
                f.write("**ERROR:**\n\n```\n" + traceback.format_exc() + "\n```\n\n")
                print("  ERROR - see eval_output.md")
            f.write("---\n\n")

    print("\nDone. Wrote eval_output.md")


if __name__ == "__main__":
    main()
