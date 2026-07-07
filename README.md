# The Unofficial Guide — CSI CS Professor Reviews (RAG)

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
| 3 | rmp_rao.txt | Jun Rao reviews |
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

<!-- TODO: fill after running app.py — describe the system prompt and source attribution -->

## Example Responses

<!-- TODO: fill after running app.py — paste 2 responses with sources + 1 out-of-scope refusal -->

## Query Interface

The interface is a Gradio web app (app.py) with two input/output areas:
- **Input:** A text box where the user types a plain-language question about CSI CS professors
- **Output:** An "Answer" box showing the grounded response with source citations, and a "Sources used" box listing which document files the answer drew from

**Sample interaction:**
<!-- TODO: paste one complete query and response after running app.py -->

## Evaluation Report

| # | Question | Expected Answer | System Response | Accuracy |
|---|----------|-----------------|-----------------|----------|
| 1 | Does Professor Shuqun Zhang help students during labs? | Yes — multiple reviews say he helps during lab sessions and stays after class. | <!-- TODO --> | <!-- TODO --> |
| 2 | Do students think Professor Fuad Alnajjar's positive reviews are trustworthy? | Mixed — most are positive, but one claims the positive reviews were written by the professor himself. | <!-- TODO --> | <!-- TODO --> |
| 3 | Does Professor Shuqun Zhang give practice exams? | Yes — a review says he does reviews before all exams and gives practice exams. | <!-- TODO --> | <!-- TODO --> |
| 4 | <!-- TODO: your question from rmp_rao.txt --> | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 5 | Where can I park near the CS building at CSI? | System should say it doesn't have enough information. | <!-- TODO --> | <!-- TODO --> |

## Failure Case

<!-- TODO: after running all 5 eval questions, describe one failure with a specific pipeline-level explanation -->

## Spec Reflection

<!-- TODO: one way the spec helped, one way implementation diverged -->

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