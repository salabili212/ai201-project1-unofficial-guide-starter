"""Answer generation backends.

The system supports two generation backends and picks whichever is available:

1. **Groq** (`meta-llama/llama-4-scout-17b-16e-instruct` or similar) — used when
   a valid GROQ_API_KEY is present in .env. This is the primary path.
2. **Local** (`Qwen/Qwen2.5-0.5B-Instruct` via transformers) — used when no API
   key is configured. Runs on CPU, no network after the first download, no
   account required.

Having a local fallback is a deliberate design choice, not just a workaround.
A RAG system whose answer stage is a single hosted API is one revoked key away
from returning nothing at all — which is exactly what happened to this project
when its original Groq key expired. Degrading to a smaller local model produces
a worse answer than the hosted one, but a worse answer built from the correct
retrieved chunks is far more useful than a stack trace.

Both backends receive an identical prompt and identical retrieved context, so
grounding is enforced the same way regardless of which one runs.
"""
import os

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

LOCAL_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

_local_pipe = None


def groq_available():
    """True only if a key is configured that looks like a real Groq key."""
    key = (os.getenv("GROQ_API_KEY") or "").strip().strip("\"'")
    return key.startswith("gsk_") and len(key) > 40


def generate_groq(user_prompt):
    """Generate via the Groq API. Requires GROQ_API_KEY."""
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY").strip().strip("\"'"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _load_local():
    """Load the local model once and cache it."""
    global _local_pipe
    if _local_pipe is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        print(f"Loading local model {LOCAL_MODEL} (first run downloads ~1 GB)...")
        tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL)
        model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL)
        _local_pipe = pipeline(
            "text-generation", model=model, tokenizer=tokenizer, device=-1
        )
        print("Local model ready.")
    return _local_pipe


def generate_local(user_prompt):
    """Generate with a small instruction-tuned model running on CPU."""
    pipe = _load_local()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    out = pipe(
        messages,
        max_new_tokens=320,
        do_sample=False,
        temperature=None,
        top_p=None,
        return_full_text=False,
    )
    return out[0]["generated_text"].strip()


def generate(user_prompt):
    """Generate an answer using whichever backend is available.

    Returns (answer_text, backend_name) so callers can report which path ran.
    """
    if groq_available():
        try:
            return generate_groq(user_prompt), "groq:llama-3.3-70b-versatile"
        except Exception as e:
            print(f"Groq call failed ({type(e).__name__}), falling back to local model.")
    return generate_local(user_prompt), f"local:{LOCAL_MODEL}"
