### 📊 RAG Evaluation

Learned how to evaluate a RAG system **layer by layer** instead of checking only the final answer.

- **Golden Dataset** – Created test cases containing a question and its **ground-truth answer**.
- **Context Evaluation**
  - **Precision** – Measures how much of the retrieved context is relevant to the query.
  - **Recall** – Measures how much of the relevant information was successfully retrieved. 
- **LLM Evaluation**
  - **Faithfulness** – Checks whether the answer is supported by the retrieved context rather than hallucinated.
  - **Correctness** – Checks whether the final answer matches the ground truth.
  - **Relevance** – Checks whether the answer actually addresses the user's question. 
- Used these **five evaluation dimensions — Precision, Recall, Faithfulness, Relevance, and Correctness —** to identify where a RAG pipeline is failing and what component needs improvement.


