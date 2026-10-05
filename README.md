# Student-Teacher Evaluation System

An AI-powered examination system where teachers upload course material, generate question papers automatically using LLM + RAG, and evaluate student answers with configurable strictness levels.

---

## How It Works (Step-by-Step)

### Step 1: Teacher Registration & Login

- Teachers register with name, email, subject, and password.
- Credentials are stored in a local SQLite database with hashed passwords.
- After login, teachers land on their dashboard where they can manage exams.

### Step 2: PDF Upload & Knowledge Base Creation

- Teacher uploads one or more PDFs (textbooks, notes, course material).
- The system extracts text from each PDF using `pdfplumber`.
- Extracted text is split into overlapping chunks (~500-1000 tokens each) using LangChain's `RecursiveCharacterTextSplitter`.
- Each chunk is converted into a vector embedding using a sentence-transformer model (e.g., `all-MiniLM-L6-v2`).
- Embeddings are stored in **ChromaDB**, a local vector database — this becomes the knowledge base for that exam.

**Why chunks?** LLMs have token limits. By chunking, we retrieve only the most relevant parts of the material when generating questions, making the output accurate and context-aware.

### Step 3: Exam Configuration

Teacher configures the question paper by setting:

| Parameter              | Example               |
|------------------------|-----------------------|
| Total Marks            | 100                   |
| Topic Weightage        | Ch1: 40%, Ch2: 30%, Ch3: 30% |
| Number of MCQs         | 20 (1 mark each)      |
| Number of Fill-in-the-Blanks | 10 (2 marks each) |
| Number of Subjective Questions | 5 (8 marks each) |

The system validates that marks distribution adds up to the total.

### Step 4: Question Paper Generation (RAG + LLM)

This is the core of the system. It uses **Retrieval-Augmented Generation (RAG)**:

1. **Retrieve**: For each topic, the system queries ChromaDB to fetch the most relevant text chunks using similarity search.
2. **Augment**: The retrieved chunks are injected into a prompt template along with the exam configuration (question types, count, marks).
3. **Generate**: The LLM (GPT-4 / Gemini / local Ollama) generates questions strictly from the provided context.

```
[Topic: "Data Structures"] + [Retrieved chunks about trees, graphs...]
    |
    v
Prompt: "Generate 5 MCQs from the following content. Each MCQ should have
         4 options with exactly one correct answer..."
    |
    v
LLM Output: Structured questions with answers
```

The system also generates a **model answer key** simultaneously, which is used later for evaluation.

### Step 5: Student Registration & Login

- Students register with name, email, roll number, and password.
- Separate authentication flow from teachers.
- After login, students see available exams assigned to them.

### Step 6: Student Answer Submission

- Students view the generated question paper on their dashboard.
- They type answers directly (for text-based submission) or upload an answer PDF.
- Answers are stored linked to the student ID and exam ID.

### Step 7: Automated Answer Evaluation

The evaluation pipeline handles each question type differently:

#### MCQ Evaluation
- **Method**: Exact match against answer key.
- Scoring: Full marks or zero — no partial credit.

#### Fill-in-the-Blanks Evaluation
- **Method**: Fuzzy string matching + keyword matching.
- Uses `fuzzywuzzy` or `rapidfuzz` for approximate matching.
- Handles spelling variations and synonyms.
- Scoring: Full or partial credit based on match ratio.

#### Subjective Answer Evaluation
- **Method**: Hybrid approach combining:
  - **Semantic Similarity**: Embed both the model answer and student answer, compute cosine similarity.
  - **LLM-based Rubric Evaluation**: Send the model answer + student answer + rubric to the LLM for detailed scoring.
- The LLM considers:
  - Key concepts covered
  - Factual accuracy
  - Depth of explanation
  - Relevance to the question

#### Evaluation Strictness Levels

The teacher selects a strictness level that adjusts scoring thresholds:

| Level  | Behavior |
|--------|----------|
| Easy   | Lenient grading — partial credit given generously, synonyms accepted freely, lower similarity threshold (~0.6) |
| Medium | Balanced grading — standard thresholds, reasonable partial credit (~0.75 similarity) |
| Hard   | Strict grading — high accuracy required, minimal partial credit, high similarity threshold (~0.85) |

### Step 8: Results & Feedback

- Per-question marks breakdown.
- AI-generated feedback explaining why marks were awarded or deducted.
- Total score with percentage.
- Teachers can review and override AI-assigned marks if needed.

---

## Project Structure

```
evaluation/
├── app.py                     # Streamlit entry point (multi-page)
├── requirements.txt           # Python dependencies
├── .env                       # API keys (OPENAI_API_KEY, etc.)
├── README.md
├── PROJECT_IDEAS.txt
│
├── config/
│   └── settings.py            # App configuration, constants
│
├── database/
│   ├── db.py                  # SQLite connection & setup
│   ├── models.py              # User, Exam, Question, Submission schemas
│   └── evaluation.db          # SQLite database file (auto-created)
│
├── auth/
│   ├── teacher_auth.py        # Teacher registration/login logic
│   └── student_auth.py        # Student registration/login logic
│
├── pdf_processing/
│   ├── extractor.py           # PDF text extraction (pdfplumber)
│   └── chunker.py             # Text chunking with LangChain
│
├── rag/
│   ├── embeddings.py          # Embedding model setup
│   ├── vector_store.py        # ChromaDB operations (store/query)
│   └── retriever.py           # Retrieval logic for question generation
│
├── generation/
│   ├── question_generator.py  # LLM-based question generation
│   ├── prompts.py             # Prompt templates for each question type
│   └── paper_builder.py       # Assembles final question paper
│
├── evaluation/
│   ├── mcq_evaluator.py       # Exact match for MCQs
│   ├── fill_evaluator.py      # Fuzzy match for fill-in-the-blanks
│   ├── subjective_evaluator.py# Semantic similarity + LLM evaluation
│   ├── scoring.py             # Marks aggregation & strictness logic
│   └── feedback.py            # AI feedback generation
│
├── pages/
│   ├── 1_Teacher_Dashboard.py # Teacher-facing Streamlit pages
│   ├── 2_Create_Exam.py       # PDF upload + exam config
│   ├── 3_Generate_Paper.py    # Question generation page
│   ├── 4_Student_Dashboard.py # Student-facing pages
│   ├── 5_Take_Exam.py         # Answer submission
│   └── 6_Results.py           # Marks & feedback display
│
└── utils/
    ├── pdf_utils.py           # Helper functions for PDF handling
    └── validators.py          # Input validation helpers
```

---

## Tech Stack

| Component          | Technology                              |
|--------------------|-----------------------------------------|
| **Frontend**       | Streamlit (multi-page app)              |
| **Backend**        | Python 3.10+                            |
| **LLM**           | OpenAI GPT-4 / Google Gemini / Ollama   |
| **Embeddings**     | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Vector Store**   | ChromaDB                                |
| **RAG Framework**  | LangChain                               |
| **PDF Parsing**    | pdfplumber                              |
| **Database**       | SQLite                                  |
| **Auth**           | streamlit-authenticator                 |
| **Fuzzy Matching** | rapidfuzz                               |

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10–3.14)
- **Redis Server** (see options below)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create or update your `.env` file:
```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://127.0.0.1:6379/0
DATABASE_URL=sqlite:///eval_app_v2.db
JWT_SECRET=super-secret-key-change-in-production-123456
```

### 4. Running Redis Locally

#### Option A: Via WSL Ubuntu (Recommended on Windows)
If using WSL on Windows:
```bash
wsl -u root service redis-server start
```
To verify Redis is reachable:
```bash
python -c "import redis; print('Redis reachable:', redis.Redis(host='127.0.0.1', port=6379).ping())"
```

#### Option B: Via Docker
```bash
docker run --name eval-redis -p 6379:6379 -d redis:7-alpine
```

#### Option C: Native Windows Standalone Executable
Download standalone `redis-server.exe` from [Microsoft Archive Redis Releases](https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip) and run it in a terminal.

---

## Running the Application

### 🚀 One-Click Auto Launcher (Windows)
Double-click [start_app.bat](file:///c:/Users/kumbh/OneDrive/Desktop/coding/eval_app/start_app.bat) or run from terminal:
```powershell
.\start_app.bat
```
This automatically launches:
1. **Terminal 1**: Redis Server (Port 6379)
2. **Terminal 2**: Celery Worker (`--pool=solo`)
3. **Terminal 3**: FastAPI Backend (Port 8000)
4. **Terminal 4**: Vite React Frontend (Port 5173)
And immediately opens both the Web App (`http://localhost:5173`) and API Documentation (`http://localhost:8000/docs`) in your default browser.

---

### Manual Setup: Running in 3 Terminals

### Terminal 1: Start Redis
```bash
wsl -u root service redis-server start
# or via docker: docker start eval-redis
```

### Terminal 2: Start Celery Background Worker
> [!IMPORTANT]
> **Windows Pool Configuration**: On Windows, Celery must run with `--pool=solo` to prevent process-fork errors.
```powershell
celery -A tasks.celery_app worker --loglevel=info --pool=solo
```

### Terminal 3: Start FastAPI Backend
```powershell
python -m uvicorn api.main:app --reload --port 8000
```
Interactive API docs are available at: `http://localhost:8000/docs`

---

## Background Tasks Architecture (Days 6–8)

Heavy PDF processing and vector embedding generation are moved out of the synchronous HTTP request lifecycle into Celery background tasks:

```
Client (Teacher)
       │
       ▼
FastAPI (POST /exams/process-pdf)
       │ 1. Save file to storage/uploads/
       │ 2. Create TaskJob in DB (QUEUED)
       │ 3. Dispatch task to Celery
       ▼
Return {"task_id": 1, "status": "QUEUED"} (Immediate, <50ms)
       │
       ▼
     Redis (Message Broker)
       │
       ▼
 Celery Worker (--pool=solo)
       │
       ├─► 1. Mark TaskJob as PROCESSING (15%)
       ├─► 2. Extract PDF text using PyMuPDF (40%)
       ├─► 3. Chunk text using RecursiveCharacterTextSplitter (65%)
       ├─► 4. Generate embeddings & store in ChromaDB (85%)
       └─► 5. Mark TaskJob as COMPLETED (100%)
       │
       ▼
Client polls GET /tasks/{task_id} -> {status: "COMPLETED", progress: 100}
```

### Background Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/exams/process-pdf` | Asynchronously upload PDF, extract text, chunk, and index into ChromaDB. Returns `task_id` immediately. |
| `POST` | `/exams/extract-pdf` | Asynchronously extract text only from PDF document. Returns `task_id` immediately. |
| `GET`  | `/tasks/{task_id}` | Poll background task status, progress (0–100%), and result metadata. |

#### Example Task Status Response:
```json
{
  "task_id": 1,
  "celery_task_id": "8f8b0304-fa73-42e1-88f5-ef8540ab36c7",
  "task_type": "full_pdf_pipeline",
  "status": "COMPLETED",
  "progress": 100,
  "message": "Document processing and knowledge base creation completed successfully",
  "error": null,
  "result_metadata": {
    "file_name": "syllabus.pdf",
    "collection_name": "exam_4c3f58a9",
    "character_count": 14500,
    "chunk_count": 24,
    "duration_seconds": 3.42
  },
  "created_at": "2026-09-05T12:00:00Z",
  "started_at": "2026-09-05T12:00:01Z",
  "completed_at": "2026-09-05T12:00:04Z"
}
```

---

## Running Automated Tests

Run the full test suite (14 unit & integration tests):
```bash
pytest tests/ -v
```
Tests cover:
- Celery configuration & registered tasks
- Task creation and immediate queueing
- PDF extraction task on test material
- SentenceTransformer & ChromaDB embedding task
- Task status endpoint polling
- Failed task handling & safe error logging
- Corrupted/invalid PDF handling
- Missing file error handling
- Database session rollback & worker safety


---

## Suggested Enhancements (My Additions)

1. **Bloom's Taxonomy Tagging** — Tag each question with its cognitive level so the teacher can ensure a balanced assessment.
2. **Answer Key Auto-Generation** — Generate model answers alongside questions for consistent evaluation.
3. **Confidence Scoring** — Show the AI's confidence in each grading decision so teachers know which answers need manual review.
4. **Plagiarism Detection** — Compare student answers against each other using cosine similarity to flag potential copying.
5. **Question Bank** — Save generated questions for reuse across exams, with filtering by topic and difficulty.
6. **Class Analytics** — Dashboard showing average scores, pass rates, and topic-wise performance breakdowns.
7. **Distractor Generation** — For MCQs, generate plausible wrong options that test actual understanding.
8. **Manual Override** — Teachers can adjust any AI-assigned mark before finalizing results.

---

## License

This project is for educational purposes.
