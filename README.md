# Week 1 – LLM Fundamentals & API Mastery 🚀

---

## 📂 Structure

```
week1/
│
├── day1/ → LLM fundamentals
├── day2/ → API calls
├── day3/ → Multi-provider usage
├── day4/ → Streaming & async
├── day5/ → Structured outputs
```

---

## 📅 What I Did

* Learned core LLM concepts: tokens, context window, temperature, roles
* Built API integrations using Groq / OpenAI-style APIs
* Worked with multiple LLM providers and compared outputs
* Implemented streaming responses and async workflows
* Used Pydantic + JSON mode for structured outputs
* Handled retries, rate limits, and basic production concerns

---

## 🚀 Mini Project — Resume Evaluator

Built an end-to-end LLM-powered system that:

* Parses PDF & Word resumes into clean text
* Extracts structured data using Pydantic schemas
* Takes a Job Description as input
* Uses LLM for intelligent matching
* Returns:

  * Match score
  * Final verdict
  * Reasoning


# 📚 Week 2 & 3 – Advanced LLM Engineering

This phase focuses on building **production-ready AI systems** beyond basic prompts.

## 🚀 What I Built

* **Prompt Engineering Apps**

  * Email Classifier
  * Article Summarizer
  * Sentiment Analyzer

* **ReAct AI Agent (from scratch)**

  * Thought → Action → Observation loop
  * Tool usage (calculator, lookup)
  * Multi-step reasoning

* **Prompt Chaining Pipelines**

  * Breaking complex tasks into smaller LLM calls
  * Conditional routing

* **Streaming CLI Chatbot**

  * Real-time responses (streaming)
  * Conversation memory
  * Token tracking

* **RAG + Semantic Search (from scratch)**

  * Built a mini RAG pipeline in Python
  * Implemented embeddings + cosine similarity
  * Created a simple semantic search engine
  * Retrieved relevant context and passed to LLM

---

## 🧠 Key Concepts Learned

* Production prompt design (6-part structure)
* ReAct (Reasoning + Acting)
* Prompt chaining for scalable systems
* Streaming + TTFT optimization
* **RAG (Retrieval-Augmented Generation)**
* **Embeddings & semantic search**

---

## 🤖 AI Portfolio (Backend Ready)

Built the backend for a **personal AI chatbot** that:

* Answers recruiter questions using my resume
* Maintains a professional tone

⚠️ Frontend is **not built yet** — backend is ready.

# 📚 Vector Databases with Qdrant

This phase focuses on scaling semantic search from small demos to **production-ready systems using vector databases**.

## 🚀 What I Built

* **Qdrant Cloud Integration (Python)**

  * Created collections with correct vector size & distance metric
  * Uploaded embeddings from previous work
  * Performed top-K similarity search

* **Production-Ready Vector Search**

  * Persistent, scalable alternative to in-memory search
  * Handles large datasets efficiently

* **Advanced Qdrant Features**

  * Rich metadata payloads (tags, audience, status, dates)
  * Filtering with:

    * `must` (AND)
    * `should` (OR)
    * `must_not` (NOT)
  * Multi-tenant data isolation (SaaS-style)
  * CRUD operations (update, delete, upsert, count)

---

## 🧠 Key Concepts Learned

* Why vector databases are essential for RAG systems
* Scaling from 100 → millions of documents
* Cosine similarity vs other distance metrics
* Metadata filtering in real-world queries
* Managed vs self-hosted vector databases

---

## 📌 Outcome

Built a **cloud-hosted semantic search system** with Qdrant that:

* Scales to millions of vectors
* Supports real production use-cases
* Mimics how modern AI apps (search, RAG, recommendations) work

---




