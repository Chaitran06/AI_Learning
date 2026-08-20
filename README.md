## Week 1 – LLM Fundamentals & API Mastery 🚀
This week focused on building a strong foundation in working with Large Language Models (LLMs) using real-world, production-style workflows.

📂 Structure
week1/
│
├── day1/ → LLM fundamentals
├── day2/ → API calls
├── day3/ → Multi-provider usage
├── day4/ → Streaming & async
├── day5/ → Structured outputs

📅 What I Did
Learned core LLM concepts: tokens, context window, temperature, roles
Built API integrations using Groq / OpenAI-style APIs
Worked with multiple LLM providers and compared outputs
Implemented streaming responses and async workflows
Used Pydantic + JSON mode for structured outputs
Handled retries, rate limits, and basic production concerns

## 🚀 Mini Project — Resume Evaluator

Built an end-to-end LLM-powered system that:

Parses PDF & Word resumes into clean text
Extracts structured data using Pydantic schemas
Takes a Job Description as input
Uses LLM for intelligent matching
Returns:
Match score
Final verdict
Reasoning
