# The Unofficial Guide — CSI CS Professor Reviews (RAG)

## Running this yourself

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

copy .env.example .env            # cp .env.example .env on macOS/Linux

python evaluate.py                # runs the 5 evaluation questions end to end
python app.py                     # Gradio interface at http://localhost:7860
```

**An API key is optional.** `.env.example` ships with `GROQ_API_KEY=` left blank
and `.env` is gitignored, so no key is ever committed to this repository. If you
add your own Groq key the system generates answers with
`llama-3.3-70b-versatile`; if you leave it blank it falls back to a small local
model (`Qwen/Qwen2.5-0.5B-Instruct`) that runs on CPU with no account and no
network after the initial download. Retrieval, grounding, and source attribution
are identical either way — only the fluency of the prose differs. See
`generator.py` and the Embedding Model section below.

## Domain and Sources

My domain is student reviews of Computer Science professors at the College of
Staten Island (CUNY). This knowledge is valuable because choosing the right
professor has a big impact on how well you learn and what grade you get, but
it's hard to find through official channels — CSI's website only lists course
descriptions and faculty bios, and says nothing about which professors explain
things clearly, how hard their exams are, whether they curve, or if attendance
matters. Students share that information in Rate My Professors reviews, and my
system makes it searchable and answerable in plain language.

All documents are Rate My Professors review pages for CSI Computer Science
professors. I copied the written review text from each professor's page into a
.txt file in the documents/ folder.

| # | Source | Description |
|---|--------|-------------|
| 1 | rmp_zelikovitz.txt | Sarah Zelikovitz reviews |
| 2 | rmp_zhang_shuqun.txt | Shuqun Zhang reviews |
| 3 | rmp_cappellari.txt | Paolo Cappellari reviews |
| 4 | rmp_mohamed.txt | Ali Mohamed reviews |
| 5 | rmp_chen.txt | Cong Chen reviews |
| 6 | rmp_zhang_xiaowen.txt | Xiaowen (Sean) Zhang reviews |
| 7 | rmp_deredita.txt | Michael D'eredita reviews |
| 8 | rmp_wang.txt | Zhiqi Wang reviews |
| 9 | rmp_alnajjar.txt | Fuad Alnajjar reviews |
| 10 | rmp_petingi.txt | Louis Petingi reviews |

## Chunking Strategy

**Chunk size:** One review per chunk (roughly 100–400 characters each).

**Overlap:** None, because each review is independent of the others.

**Reasoning:** My documents are lists of short student reviews, so I split at
review boundaries instead of a fixed character count. A fixed size like 500
characters would cut reviews in the middle, creating fragments that don't
match queries well. Since many reviews don't mention the professor by name, my
chunking code prepends the professor's name to every chunk so each one can
stand alone and be attributed to the right person. Total chunks: 107.

## Sample Chunks

**Chunk 1** (source: rmp_alnajjar.txt)
> Professor Fuad Alnajjar: Outstanding professor for telecom and networking! He breaks down complex topics in a clear, easy-to-understand way and does a great job linking theory to real-world applications. Highly recommended. He is a nice professor who tries to help students.

**Chunk 2** (source: rmp_chen.txt)
> Professor Cong Chen: Don't take this guy!!! he's the worse professor i've ever taken and he doesn't know how to explain the content he teaches.

**Chunk 3** (source: rmp_chen.txt)
> Professor Cong Chen: If you want to learn algorithms take this professor. He doesn't teach code, he teaches concepts that are very important for cs professors. Attendence isnt mandatory but if you want to learn you have to attend. Probably the best CS class and one of the best professors in the department. He will be hard but it will be worth it

**Chunk 4** (source: rmp_mohamed.txt)
> Professor Ali Mohamed: Chill professor. Highly recommend taking their section for digital circuits. The content for digital circuits can be difficult and heavy, but Professor Ali structurally breaks down the concepts for easier understanding. Do attend the lectures as the procedures that are taught will be carried over into exams and HW's.

**Chunk 5** (source: rmp_zhang_shuqun.txt)
> Professor Shuqun Zhang: The professor knows and explains the subject very well. Need to write lab reports. He stayed after the class to help me when I couldn't finish during the lab time.

## Embedding Model

**Model:** all-MiniLM-L6-v2 via sentence-transformers (runs locally, no API key
or rate limits).

**Production tradeoff reflection:** For real users I would weigh: (1) accuracy
on informal text — student reviews are full of slang, typos, and abbreviations,
so a model trained on informal text could retrieve more accurately; (2) local
vs. API — an API model may be more accurate but adds cost and per-query latency,
while a local model is free and private.

## Retrieval Test Results

**Query 1:** "Does Professor Shuqun Zhang help students during labs?"
- Top chunk (distance: 0.559): "Professor Shuqun Zhang: The professor knows and explains the subject very well. Need to write lab reports. He stayed after the class to help me when I couldn't finish during the lab time."
- **Why relevant:** Directly answers the question — mentions staying after class to help during lab time. All 5 results came from rmp_zhang_shuqun.txt (except one from Xiaowen Zhang), showing retrieval correctly identified the right professor.

**Query 2:** "What do students say about Professor Chen's exams?"
- Top chunk (distance: 0.532): "Professor Cong Chen: Honestly goated professor. Hes really tough but if you want to learn this is the professor to go to. Attend the lecture and pay attention to the questions and stuff he says because most of the stuff he talks about will be on the test."
- **Why relevant:** Directly discusses exam content and preparation strategy for Chen's classes. All 5 results came from rmp_chen.txt.

**Query 3:** "Is Professor Ali Mohamed a good teacher?"
- Top chunk (distance: 0.485): "Professor Ali Mohamed: THE MOST HARDWORKING PROFESSOR. HE WILL NEVER TAKE A SHORTCUT IN YOUR CLASS. IS THE BEST"
- All 5 results from rmp_mohamed.txt, showing a range of positive and mixed opinions.

## How Grounding Is Enforced

Grounding is enforced in two places — the prompt, and the pipeline structure
around it. The prompt alone isn't enough, because an instruction is something a
model can drift from.

**1. The context window contains nothing but retrieved chunks.** `ask()` in
`query.py` builds the context string by iterating over the top-5 chunks returned
by ChromaDB and nothing else. The model is never handed the full corpus, a
summary, or any text it didn't retrieve. If a fact isn't in those five chunks, it
isn't in the prompt.

**2. The system prompt states the constraint as a rule, not a preference.**
`SYSTEM_PROMPT` tells the model to answer **only** from the provided reviews, to
cite which professor and source file each claim comes from, and — the important
one — gives it an exact refusal string to use when the reviews don't cover the
question: *"I don't have enough information to answer that based on the available
reviews."* Specifying the exact sentence matters. "Say you don't know" invites the
model to hedge into a plausible-sounding general answer; a fixed string gives it a
concrete action to take instead of guessing.

There's a fourth rule that isn't about grounding but is about honesty: the model
is told to represent the range of student opinion rather than cherry-picking. On a
corpus of Rate My Professors reviews, where a professor can have five glowing
reviews and one scathing one, summarizing only the majority view would be
technically grounded and still misleading.

**3. Source attribution is computed, not generated.** `ask()` collects source
filenames from each retrieved chunk's ChromaDB metadata and returns them as a
separate `sources` list, which `app.py` renders in its own "Sources used" box.
The model is asked to cite inline as well, but the box is not the model's output —
it's derived from retrieval metadata. Even if the model cited nothing, or cited a
file that wasn't retrieved, the interface would still show the true provenance of
the context it was given. Attribution can't be hallucinated because the model
isn't the one producing it.

The remaining weakness, which I'd want to close before calling this
production-ready: nothing verifies that a specific *sentence* in the answer traces
to a specific retrieved chunk. Grounding is enforced at the level of "the model
only saw these five chunks," not "this claim came from chunk 3."

## Example Responses

<!-- TODO: fill after running app.py — paste 2 responses with sources + 1 out-of-scope refusal -->

## Query Interface

The interface is a Gradio web app (app.py) with two input/output areas:
- **Input:** A text box where the user types a plain-language question about CSI CS professors
- **Output:** An "Answer" box showing the grounded response with source citations, and a "Sources used" box listing which document files the answer drew from

**Sample interaction:**
<!-- TODO: paste one complete query and response after running app.py -->

## Evaluation Report

Retrieval for all five questions was captured by `evaluate.py`, which writes the
full top-5 chunk list with distance scores to `eval_output.md`. Sources retrieved
per question:

| # | Sources retrieved (top-5, with distances) | Retrieval verdict |
|---|---|---|
| 1 | `zhang_shuqun` ×4 (0.559, 0.619, 0.647, 0.723), `zhang_xiaowen` ×1 (0.701) | Accurate — 4 of 5 from the right professor |
| 2 | `alnajjar` ×4 (0.611, 0.807, 0.933, 1.055), `chen` ×1 (1.054) | Accurate — the skeptical review is retrieved alongside the positive ones |
| 3 | `zhang_shuqun` ×3 (0.745, 0.754, 0.830), `zhang_xiaowen` ×2 (0.807, 0.807) | Partially accurate — surname collision pulls in the wrong Zhang |
| 4 | `cappellari` ×2 (0.684, 0.843), `mohamed` ×2 (1.012, 1.033), `petingi` ×1 (1.105) | Partially accurate — both relevant chunks found, then padded with noise |
| 5 | `mohamed` ×3, `zelikovitz` ×1, `alnajjar` ×1 — all at distance 1.40–1.50 | Correctly finds nothing relevant; distances flag it clearly |

| # | Question | Expected Answer | System Response | Accuracy |
|---|----------|-----------------|-----------------|----------|
| 1 | Does Professor Shuqun Zhang help students during labs? | Yes — multiple reviews say he helps during lab sessions and stays after class. | <!-- TODO --> | <!-- TODO --> |
| 2 | Do students think Professor Fuad Alnajjar's positive reviews are trustworthy? | Mixed — most are positive, but one claims the positive reviews were written by the professor himself. | <!-- TODO --> | <!-- TODO --> |
| 3 | Does Professor Shuqun Zhang give practice exams? | Yes — a review says he does reviews before all exams and gives practice exams. | <!-- TODO --> | <!-- TODO --> |
| 4 | What do students say about Professor Paolo Cappellari's homework load and flexibility? | Split — one review calls him clear and straightforward but notes a lot of homework plus a group project (waivers given at the end); the other calls him inflexible, closing submission links the moment work is late regardless of technical difficulties. | <!-- TODO --> | <!-- TODO --> |
| 5 | Where can I park near the CS building at CSI? | System should say it doesn't have enough information. | <!-- TODO --> | <!-- TODO --> |

## Failure Case

### Primary failure: two professors share a surname, and retrieval merges them

**The query:** "Is Professor Zhang a good teacher?"

I predicted this one in `planning.md` under Anticipated Challenges, and running it
confirmed it. My corpus contains two different professors named Zhang — Shuqun
Zhang and Xiaowen (Sean) Zhang. Retrieval returns a blend of both:

| Rank | Source | Distance |
|---|---|---|
| 1 | `rmp_zhang_xiaowen.txt` | 0.511 |
| 2 | `rmp_zhang_shuqun.txt` | 0.521 |
| 3 | `rmp_zhang_xiaowen.txt` | 0.595 |
| 4 | `rmp_zhang_xiaowen.txt` | 0.678 |
| 5 | `rmp_zhang_shuqun.txt` | 0.685 |

Three chunks about one professor, two about another, and the retrieved text is
flatly contradictory: chunk 1 says *"Excellent professor who was always very
helpful during and after class,"* while chunk 3 says *"Could not teach clearly if
his life depended on it... Most of the class dropped out, do not take him."* Both
statements are true — of different people.

**Why it happens, specifically:** it's a chunking decision, not a retrieval bug.
My chunker prepends the professor's full name to every chunk so each one is
self-describing (`ingest.py`, `make_chunks()`). That works well when a query names
a professor uniquely — it's why the Cappellari and Mohamed queries retrieve
cleanly. But the embedding is a single dense vector over the whole chunk, and
"Professor Shuqun Zhang" and "Professor Xiaowen (Sean) Zhang" are lexically and
semantically near-identical strings. The surname dominates the name portion of the
embedding and the disambiguating first name contributes very little to overall
similarity. The distances confirm it: ranks 1 and 2 are 0.010 apart across two
*different* professors. The embedding has no way to express "these are different
people" because nothing in my pipeline ever told it they were — I encoded
identity as free text inside the chunk rather than as structured metadata.

The downstream consequence is the part that matters. Retrieval returning a mix
isn't itself wrong — the query genuinely is ambiguous. The failure is that the
generation stage has no way to *notice* the mix. All five chunks arrive as
undifferentiated context, so the model will synthesize one answer about "Professor
Zhang" that averages two people into a single incoherent verdict, and it will be
correctly sourced while being wrong.

**The fix I'd make:** the professor name is already known at ingestion time — it's
the `NAMES` lookup — but it's only written into the chunk text, not into the
metadata dict, which currently holds just `source` and `position`. Adding
`professor` as a metadata field would let me either filter by professor when a
query names one unambiguously, or detect at query time that retrieved chunks span
more than one professor and have the interface ask which Zhang the user meant
rather than guessing. That's a metadata-filtering change, which is also one of the
listed stretch features — I ran out of time before implementing it, but this
failure is the concrete argument for why it's worth doing.

### Secondary observation: fixed top-k pads thin coverage with noise

The Cappellari query surfaced a second, milder version of the same class of
problem. Cappellari has only two reviews in my corpus. Retrieval returns both
correctly at ranks 1 and 2 (distances 0.684 and 0.843) — and then, because `k` is
hardcoded to 5, fills the remaining three slots with reviews about Ali Mohamed and
Louis Petingi at distances 1.012, 1.033, and 1.105.

Those three chunks are on-topic in the abstract — they're all about homework load
and deadline flexibility, which is what I asked about — but they're about the
wrong professor. This is the "uneven coverage" risk from `planning.md` showing up
with numbers attached. A distance threshold (drop anything above ~1.0) alongside
top-k would return two chunks here instead of five, and the answer would be built
only from material that's actually about Cappellari.

The same gap shows in the out-of-scope parking query: every retrieved chunk sits
at distance 1.40–1.50, unmistakably irrelevant, yet the pipeline still forwards all
five to the LLM and relies entirely on the prompt's refusal instruction to catch
it. Retrieval already *knows* nothing matched. It just has no way to say so.

## Spec Reflection

**Where the spec helped:** writing the chunking strategy before any code forced me
to look at what my documents actually were, and they turned out to be lists of
short independent reviews rather than continuous prose. That one observation
decided two things at once. It ruled out fixed-character chunking, because a
500-character window would cut a review in half and leave a fragment like
"Professor Smith's exams are heavily" with no standalone meaning. And it ruled out
overlap entirely — overlap exists to keep a fact from being split across a
boundary, but if the boundary is a review boundary, there's no fact spanning it.
Overlap here would just have duplicated whole reviews into neighboring chunks and
made the same opinion match a query several times. Having written that down first,
the implementation was a short function rather than a round of guessing, and I
never had to tune a chunk size.

**Where the implementation diverged:** the spec said the professor's name would be
prepended to each chunk "from each file's header line." When I actually processed
the documents, the header lines were inconsistent — some files had them, some
didn't, and the ones that did weren't formatted the same way. Parsing them would
have meant a fragile rule that silently mislabeled chunks whenever a file didn't
match the expected shape, and a mislabeled chunk is worse than a missing one,
because it attributes a real review to the wrong professor. So I moved the mapping
out of the document content and into an explicit `NAMES` dictionary in `ingest.py`
keyed by filename, and made an unmapped file print a warning and skip rather than
guess. The chunking *strategy* was unchanged — one review per chunk, name
prepended, no overlap — but the source of the name moved from "parsed from data"
to "declared in code."

That tradeoff is worth naming, because it isn't free: `NAMES` is a hardcoded map
that has to be updated by hand every time a document is added, which doesn't scale
past a corpus this size. What it buys is that the failure mode is loud. A missing
entry prints `WARNING: <file> not in NAMES map — skipped` instead of quietly
attributing reviews to the wrong person. At eleven documents that's the right
trade; at a few hundred I'd need a real parsing strategy with validation, not a
dictionary.

Worth noting for anyone extending this: `NAMES` currently has eleven entries but
`documents/` has ten files. The extra entry (`rmp_rao.txt`) is a professor I
planned to include and didn't end up collecting. It's harmless — the map is only
read by filename lookup, so an unused key does nothing — but it's exactly the kind
of drift between spec and data that the warning above is designed to catch in the
other direction.

## AI Usage

**Instance 1 — Ingestion and chunking:** I gave Claude my Chunking Strategy
section and asked it to write a Python script that loads .txt files from
documents/ and splits them into one chunk per review with the professor's name
prepended. The first version assumed files had header lines and split on
numbered lines or blank lines — it produced only 21 chunks with reviews mashed
together. I had Claude rewrite it to derive professor names from filenames and
split on single line breaks instead, which correctly produced 107 chunks.

**Instance 2 — Embedding and retrieval:** I gave Claude my Retrieval Approach
section and asked it to embed chunks with all-MiniLM-L6-v2 and store them in
ChromaDB with source metadata, plus a retrieval function returning top-5
chunks. The generated code worked on the first try. I tested with 3 evaluation
queries and verified the returned chunks were relevant and from the correct
professor files.

## Demo Video

<!-- TODO: link to your 3-5 minute demo video -->