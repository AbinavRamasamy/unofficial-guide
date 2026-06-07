# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official course descriptions don't reflect teaching style, exam difficulty, or workload." -->
Course and professor reviews at Rutgers-New Brunswick - useful because students need candid, experience-based feedback on teaching quality, workload, and grading to make informed decisions.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors — Rutgers NB | Professor ratings | https://www.ratemyprofessors.com/school/825 |
| 2 | r/rutgers — professor review threads | Reddit RSS | https://www.reddit.com/r/rutgers/search.rss?q=professor+review |
| 3 | r/rutgers — which professor threads | Reddit RSS | https://www.reddit.com/r/rutgers/search.rss?q=which+professor+should+I+take |
| 4 | r/rutgers — course difficulty threads | Reddit RSS | https://www.reddit.com/r/rutgers/search.rss?q=course+hard+easy+grade |
| 5 | r/rutgers — finals/midterm threads | Reddit RSS | https://www.reddit.com/r/rutgers/search.rss?q=final+exam+midterm |
| 6 | r/rutgers — course evaluation threads | Reddit RSS | https://www.reddit.com/r/rutgers/search.rss?q=course+evaluation |
| 7 | Rutgers CS course descriptions | Course catalog | https://www.cs.rutgers.edu/academics/undergraduate/course-synopses |
| 8 | Rate My Professors — Rutgers Math/Stats | Professor ratings | https://www.ratemyprofessors.com/search/professors/825?q=mathematics |
| 9 | Koofers — Rutgers NB professors | Grade distributions | https://www.koofers.com/rutgers-the-state-university-of-new-jersey-new-brunswick/professors |
| 10 | Rutgers Webreg course listings | Course sections | https://sims.rutgers.edu/webreg/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 250 tokens

**Overlap:** 0

**Why these choices fit your documents:** Each source document is one standalone Reddit post or review. A 250-token chunk fits one full post without splitting it, so overlap isn't needed — there's no long document being cut across boundaries.

**Final chunk count:** 586

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint, what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text, latency, and local vs. API-hosted. -->

**Model used:** all-MiniLM-L6-v2

**Production tradeoff reflection:** all-MiniLM-L6-v2 is fast, free, and runs locally with no API dependency. Its 256-token context limit fits the chunk size and it handles short review text well. The tradeoff is lower semantic accuracy on informal language — it can miss nuanced signals like "the curve saved me" or "attendance tanked my grade." A larger model like text-embedding-3-small would improve retrieval quality at the cost of per-token API fees and added latency.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain the mechanism. -->

**System prompt grounding instruction:** The system prompt uses hard constraints, not suggestions: "Answer questions using ONLY the information provided in the CONTEXT section below. You must not use any outside knowledge, even if you are confident in it." It also specifies an exact fallback phrase — "I don't have enough information on that in my sources." — so the model cannot produce a vague non-answer while still sounding helpful. Temperature is set to 0.2 to reduce creative drift from the retrieved context.

**How source attribution is surfaced in the response:** Sources are appended programmatically in Python after the LLM responds, not generated by the model. A `format_sources()` function deduplicates the retrieved chunks by URL and builds the source list from their metadata. This guarantees sources are always present and always accurate regardless of what the LLM outputs.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Having the chunking strategy written down before coding meant I didn't have to make judgment calls mid-implementation. When the AI initially generated a 320-token chunk size, I had a concrete spec to compare against — I knew 250 was the right number because I had already reasoned through the average review length. Without the spec, I would have just accepted whatever the AI produced.

**One way your implementation diverged from the spec, and why:** The spec listed FAISS as the vector store and the architecture diagram reflected that. During implementation I switched to ChromaDB because it was already in the project's requirements.txt and handles both storage and similarity search in one library — FAISS would have required a separate storage layer for the chunk text and metadata. The spec diagram was updated to reflect the change. 

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement chunk_text(). It returned a function using a fixed character split. I overrode the chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* The Documents table from planning.md and the Chunking Strategy section, and asked it to implement `scrape_documents()` and `chunk_text()`.
- *What it produced:* A scraper using PRAW (Reddit's API library) with credentials, and a chunker with a 320-token chunk size.
- *What I changed or overrode:* PRAW required creating a Reddit bot account which kept failing, so I redirected the AI to use Reddit's RSS feed instead — no credentials needed. I also reduced the chunk size from 320 to 250 tokens because most reviews are under 150 words and 320 risked bundling two separate reviews into one chunk, which would introduce noise during retrieval.

**Instance 2**

- *What I gave the AI:* The Architecture diagram and Retrieval Approach section, and asked it to implement the generation step with Groq and source attribution.
- *What it produced:* A `generate()` function that returned answer and sources as a single combined string, and a system prompt that used soft language ("try to use the documents").
- *What I changed or overrode:* I told the AI to split the return into a tuple so answer and sources could be displayed in separate UI boxes. I also pushed back on the system prompt wording — changed "try to use" to "ONLY" and "must not" to make grounding a hard constraint rather than a suggestion, and added the exact fallback phrase so the model couldn't hedge its way around it.
