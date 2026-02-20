# Fitness Coach Bot — RAG Implementation Master Prompt

> **How to use this document:** Copy the prompt under each phase into a new Claude chat when you are ready to start that phase. Each phase prompt is self-contained and tells Claude to verify your progress before moving on. Work through the phases in order.

---

## Architecture Overview

### System Design: Naive RAG (Simple & Appropriate for This Project)

```
┌─────────────────────────────────────────────────────────────────┐
│                        OFFLINE (one-time)                       │
│                                                                 │
│  CSV Datasets ──► Chunk & Clean ──► Embed ──► ChromaDB Store   │
│  (exercises +                     (OpenAI                       │
│   nutrients)                       Ada-002)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ONLINE (per request)                      │
│                                                                 │
│  User Input         Query ChromaDB        LLM Call             │
│  (profile form) ──► (top-k exercises  ──► GPT-4o-mini ──► Plan │
│                      + nutrients)          + safety prompt      │
│                                                                 │
│  Streamlit UI ◄──────────────────────────────────────────── ◄─┘│
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Choice: Naive RAG
**Why Naive RAG?** It is the simplest proven pattern: retrieve → augment → generate. No query rewriting, no re-ranking, no agents. This keeps the project focused and easy to explain in your report. It is the right choice given your timeline and the structured nature of the dataset (exercises + nutrients are factual rows, not long documents).

### Folder Structure
```
fitness-coach-bot/
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── api.py               # FastAPI routes
│   ├── rag/
│   │   ├── ingest.py        # Load & embed datasets → ChromaDB
│   │   ├── retriever.py     # Query ChromaDB
│   │   └── chain.py         # LangChain chain (prompt + LLM)
│   ├── prompts/
│   │   └── system_prompt.py # System + safety instructions
│   └── utils/
│       └── calorie_calc.py  # BMR / TDEE math
├── data/
│   ├── gym_exercise_data.csv
│   └── nutrients.csv
├── chroma_db/               # Persisted vector store (gitignored)
├── requirements.txt
├── .env                     # API keys (gitignored)
└── README.md
```

### Request Flow (step by step)
1. User fills profile form in **Streamlit** (height, weight, age, goal, dietary restrictions, plan duration).
2. Streamlit sends a POST request to **FastAPI** `/generate-plan`.
3. FastAPI calls the **retriever** — queries ChromaDB with terms like `"chest push exercises beginner"` and `"high protein low carb meals"`.
4. Top-k results (exercises + nutrients) are injected into a **LangChain prompt template**.
5. The assembled prompt is sent to **GPT-4o-mini** via the LangChain LLM chain.
6. The model returns a structured workout + meal plan with calorie breakdown.
7. FastAPI returns the plan JSON → Streamlit renders it.

---

## Phase 0 — Environment Setup

### Prompt to paste into Claude:

```
You are a senior Python developer helping me build a RAG-based fitness chatbot step by step.
My stack is: Streamlit, LangChain, ChromaDB, FastAPI, OpenAI API (gpt-4o-mini), hosted on Hugging Face Spaces.

## Your role
Guide me through Phase 0: Environment Setup only.
Give me one small actionable step at a time.
After each step, ask me to confirm it worked before giving the next step.
Do NOT skip ahead or bundle multiple steps.

## Phase 0 Goals
1. Create the project folder structure shown below.
2. Create and activate a Python virtual environment (Python 3.10).
3. Create requirements.txt with all dependencies.
4. Create a .env file template with placeholder keys.
5. Verify everything installs cleanly.

## Folder structure to create:
fitness-coach-bot/
├── app/
│   ├── main.py
│   ├── api.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── retriever.py
│   │   └── chain.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system_prompt.py
│   └── utils/
│       ├── __init__.py
│       └── calorie_calc.py
├── data/
├── chroma_db/
├── requirements.txt
├── .env
└── README.md

## Dependencies to include in requirements.txt:
streamlit==1.35.0
fastapi==0.111.0
uvicorn==0.30.1
langchain==0.2.5
langchain-openai==0.1.8
langchain-community==0.2.5
chromadb==0.5.3
openai==1.35.0
python-dotenv==1.0.1
pandas==2.2.2
tiktoken==0.7.0
httpx==0.27.0
pydantic==2.7.4
requests==2.32.3

## .env template:
OPENAI_API_KEY=your_key_here

## Start with step 1. After I confirm each step works, give me the next one.
```

---

## Phase 1 — Data Ingestion & ChromaDB Setup

### Prompt to paste into Claude:

```
You are a senior Python developer helping me build a RAG-based fitness chatbot.
I have completed Phase 0 (environment setup). My folder structure and requirements are ready.

## Your role
Guide me through Phase 1: Data Ingestion only.
Give me one small actionable step at a time.
After each step, tell me exactly how to verify it worked (what to run, what output to expect).
Do NOT move to the next step until I confirm the current step is working.

## Phase 1 Goals
1. Load the Kaggle gym exercise CSV (columns: Title, Desc, Type, BodyPart, Equipment, Level, Rating, RatingDesc).
2. Load the nutrients CSV (columns: name, calories, protein, fat, carbohydrates, fiber).
3. Clean and chunk the data into LangChain Documents — one Document per exercise row, one per food row.
4. Generate embeddings using OpenAI text-embedding-ada-002 via LangChain.
5. Persist two ChromaDB collections: "exercises" and "nutrients".
6. Write a quick test script that queries each collection and prints 3 results.

## Important constraints:
- File to write: app/rag/ingest.py
- Use LangChain's Chroma vector store wrapper (from langchain_community.vectorstores import Chroma)
- Use OpenAIEmbeddings from langchain_openai
- Persist ChromaDB to ./chroma_db directory
- Each Document's page_content should be a plain English sentence describing the item, e.g.:
  Exercise: "Barbell Bench Press targets Chest, equipment: Barbell, level: Beginner. Description: ..."
  Nutrient: "Chicken Breast: 165 calories, 31g protein, 3.6g fat, 0g carbs per 100g."
- The script should be runnable as: python -m app.rag.ingest
- After ingestion print: "✅ Ingested X exercises and Y nutrients into ChromaDB."

## Verification test I'll run:
python -c "
from app.rag.retriever import query_exercises, query_nutrients
print(query_exercises('chest push beginner barbell', k=3))
print(query_nutrients('high protein low fat', k=3))
"

## Start with step 1. After I confirm each step works, give me the next one.
```

---

## Phase 2 — Calorie Calculator & Safety Utils

### Prompt to paste into Claude:

```
You are a senior Python developer helping me build a RAG-based fitness chatbot.
Phases 0 and 1 are complete. ChromaDB is populated and queryable.

## Your role
Guide me through Phase 2: Calorie Calculation & Safety Layer only.
One step at a time. Verify before continuing.

## Phase 2 Goals
1. Implement BMR using the Mifflin-St Jeor equation in app/utils/calorie_calc.py.
2. Implement TDEE = BMR × activity multiplier.
3. Implement calorie targets per goal:
   - lose weight: TDEE - 500
   - gain weight / bulk: TDEE + 300
   - maintain: TDEE
   - The system must REJECT any result below 1200 kcal/day (safety floor) and warn the user.
4. Write the system prompt in app/prompts/system_prompt.py with:
   - Persona: "You are FitBot, a certified fitness and nutrition assistant."
   - Scope limiter: refuse to diagnose injuries or medical conditions.
   - Safety rule: never suggest a caloric deficit greater than 500 kcal/day.
   - Safety rule: always recommend consulting a doctor before starting a new program.
   - ED safety rule: if the user's calculated calories fall below 1200 kcal for any reason, output a warning message instead of the plan and suggest they speak to a healthcare professional.
   - Output format instruction: always return a structured plan with clearly labeled sections: CALORIE SUMMARY, WORKOUT PLAN, MEAL PLAN.

## Inputs to calorie_calc.py:
- weight_kg: float
- height_cm: float  
- age: int
- sex: str ("male" | "female")
- activity_level: str ("sedentary" | "light" | "moderate" | "active" | "very_active")
- goal: str ("lose" | "gain" | "maintain" | "bulk")

## Returns: dict with keys: bmr, tdee, target_calories, warning (str or None)

## Verification: write and run a small unit test with known values.

## Start with step 1.
```

---

## Phase 3 — LangChain RAG Chain

### Prompt to paste into Claude:

```
You are a senior Python developer helping me build a RAG-based fitness chatbot.
Phases 0-2 are complete. ChromaDB works, calorie calculator works, system prompt is written.

## Your role
Guide me through Phase 3: LangChain RAG Chain only.
One step at a time. Verify before continuing.

## Phase 3 Goals
1. Write app/rag/retriever.py with two functions:
   - query_exercises(query: str, k: int = 5) -> list[str]  — returns page_content strings
   - query_nutrients(query: str, k: int = 5) -> list[str]
2. Write app/rag/chain.py that:
   - Accepts a user_profile dict (weight, height, age, sex, goal, activity_level, dietary_restrictions, plan_duration, target_calories).
   - Builds a smart retrieval query from the profile (e.g. goal + muscle groups).
   - Retrieves top-5 exercises and top-5 food items from ChromaDB.
   - Assembles a LangChain ChatPromptTemplate with:
     * system message = the system prompt from Phase 2
     * human message = profile + retrieved context + instruction to generate the plan
   - Calls GPT-4o-mini via ChatOpenAI (temperature=0.3, max_tokens=1500).
   - Returns the raw string response.
3. Write a standalone test: python -m app.rag.chain and print the result for a sample profile.

## Sample test profile:
{
  "weight_kg": 70, "height_cm": 170, "age": 25, "sex": "female",
  "goal": "lose", "activity_level": "moderate",
  "dietary_restrictions": "vegetarian", "plan_duration": "weekly",
  "target_calories": 1650
}

## Expected output: a readable plan with CALORIE SUMMARY, WORKOUT PLAN, MEAL PLAN sections.

## Constraint: use LangChain's LCEL syntax (chain = prompt | llm) not the deprecated LLMChain.

## Start with step 1.
```

---

## Phase 4 — FastAPI Backend

### Prompt to paste into Claude:

```
You are a senior Python developer helping me build a RAG-based fitness chatbot.
Phases 0-3 are complete. The RAG chain generates correct plans from a Python script.

## Your role
Guide me through Phase 4: FastAPI Backend only.
One step at a time. Verify before continuing.

## Phase 4 Goals
1. Write app/api.py with:
   - POST /generate-plan endpoint
   - Request body (Pydantic model): weight_kg, height_cm, age, sex, goal, activity_level, dietary_restrictions (list[str]), plan_duration ("daily" | "weekly")
   - Internally call calorie_calc, then chain.generate_plan()
   - Return JSON: { "plan": str, "calories": { "bmr": int, "tdee": int, "target": int }, "warning": str|null }
   - GET /health → { "status": "ok" }
2. Add proper error handling (400 for validation errors, 500 for LLM errors).
3. Add CORS middleware (allow all origins for development).
4. Verify with: uvicorn app.api:app --reload
   Then test with curl or the auto-generated Swagger UI at http://localhost:8000/docs.

## Verification curl command I'll run:
curl -X POST http://localhost:8000/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"weight_kg":70,"height_cm":170,"age":25,"sex":"female","goal":"lose","activity_level":"moderate","dietary_restrictions":["vegetarian"],"plan_duration":"weekly"}'

## Start with step 1.
```

---

## Phase 5 — Streamlit Frontend

### Prompt to paste into Claude:

```
You are a senior Python developer helping me build a RAG-based fitness chatbot.
Phases 0-4 are complete. FastAPI is running and returning correct plans.

## Your role
Guide me through Phase 5: Streamlit Frontend only.
One step at a time. Verify before continuing.

## Phase 5 Goals
Write app/main.py as the Streamlit UI with these sections:

1. Header: "🏋️ FitBot — Your Personal Fitness Coach"
2. Sidebar form with:
   - Weight (kg) — number input
   - Height (cm) — number input
   - Age — number input
   - Sex — selectbox (Male / Female)
   - Fitness Goal — selectbox (Lose Weight / Gain Weight / Maintain / Bulk)
   - Activity Level — selectbox (Sedentary / Lightly Active / Moderately Active / Active / Very Active)
   - Dietary Restrictions — multiselect (Vegetarian, Vegan, Gluten-Free, Dairy-Free, Halal, None)
   - Plan Duration — radio (Daily / Weekly)
   - "Generate My Plan 🚀" button
3. Main area:
   - Show a spinner while waiting for the API.
   - Display a calorie summary card (BMR / TDEE / Target).
   - If there is a warning, show it in a red st.warning box BEFORE the plan.
   - Display the plan in st.markdown() for clean formatting.
4. The UI should call FastAPI at http://localhost:8000/generate-plan.
5. To run: streamlit run app/main.py

## Constraint: keep it clean and readable. No custom CSS needed.
## Verification: open the browser, fill the form, click generate, see a formatted plan appear.

## Start with step 1.
```

---

## Phase 6 — Hugging Face Spaces Deployment

### Prompt to paste into Claude:

```
You are a senior Python developer helping me deploy a Streamlit + FastAPI fitness chatbot to Hugging Face Spaces.
All local development is complete and working.

## Your role
Guide me through Phase 6: Deployment only.
One step at a time. Verify before continuing.

## Phase 6 Goals
1. Create a Hugging Face Space (Streamlit SDK).
2. Restructure the app so Streamlit and FastAPI run together using a startup script.
3. Create a requirements.txt for HF Spaces (same as local, verify versions).
4. Add the OpenAI API key as a HF Space Secret (not hardcoded).
5. Handle ChromaDB persistence: run ingest.py on first startup, persist to disk.
6. Create README.md with:
   - Project description
   - How to use
   - Architecture diagram (text-based)
   - Dataset credits
7. Push to HF Spaces using git.
8. Verify the live URL works end to end.

## Important: HF Spaces uses port 7860. The startup must:
   - Launch FastAPI on port 8000 in the background
   - Launch Streamlit on port 7860 in the foreground
   - This is typically done with a shell script run by the Dockerfile or app.py entry point.

## Start with step 1.
```

---

## Blog Post Outline (for Documentation)

Use this structure for your project blog post:

```
Title: Building a RAG-Powered Fitness Coach Bot with LangChain, ChromaDB & GPT-4o-mini

1. Introduction — The problem: generic fitness plans don't work
2. Architecture — Naive RAG diagram + why we chose it
3. The Data — Kaggle gym dataset + nutrients dataset, how we preprocessed it
4. Retrieval — How ChromaDB finds the right exercises for your profile
5. The Prompt — System instructions, safety layer, Chain-of-Thought for calorie math
6. The App — Streamlit UI walkthrough with screenshots
7. Safety Considerations — ED safeguards, medical disclaimer, calorie floor
8. What We Learned — Prompt engineering, RAG tradeoffs, API cost management
9. Future Work — Progress tracking, wearable integration, image analysis
10. Conclusion
```

---

## RAG Architecture Description (for Project Report)

**Architecture Name:** Naive RAG (Retrieve-Augment-Generate)

**Components:**
- **Document Store:** Two ChromaDB collections — `exercises` (gym dataset) and `nutrients` (food dataset)
- **Embedding Model:** OpenAI `text-embedding-ada-002` for both ingestion and query-time embedding
- **Retriever:** Cosine similarity search, top-5 results per collection
- **Augmentation:** Retrieved documents injected into a LangChain `ChatPromptTemplate` as context
- **Generator:** GPT-4o-mini with temperature=0.3 for consistent, structured outputs
- **Safety Layer:** System prompt enforces persona, scope, and calorie safety floors

**Why Naive RAG over other patterns?**
The dataset is small and structured (tabular rows), so complex patterns like Self-RAG, Corrective RAG, or Agentic RAG would add complexity without meaningful benefit. Naive RAG is transparent, easy to evaluate, and sufficient for generating grounded fitness plans from a fixed knowledge base. This is the honest choice for a course project and demonstrates understanding of the RAG pattern without over-engineering.

---

## Quick Reference — Key Safety Rules to Implement

| Rule | Where | Implementation |
|------|--------|----------------|
| Never diagnose injuries | System prompt | Explicit refusal instruction |
| Never exceed 500 kcal deficit | System prompt + calc | Both layers |
| Calorie floor 1200 kcal/day | calorie_calc.py | Raise warning, block plan |
| Always recommend doctor consult | System prompt | Appended to every response |
| Refuse off-topic medical questions | System prompt | Scope limiter instruction |
| No dangerous supplement advice | System prompt | Explicit prohibition |
