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

## Day 18 AI Agent Prompt
I am making an ai agent using groq llm which can do two things: web search and maths calculations for basic operations. I want to define 2 tools for this, once will be web search which will use tavily, i have the tavily api key in my env file as TAVILY_API_KEY. it sshould take a query and return the answer by web search.

2nd tool is a function calculate which takes a string expression like 2*2 and gives a answer, both the tools will be python functions.

For llm i will be using groq and the model i will be using is openai/gpt-oss-120b

the tool should be auto and we should have tools object which contains both my tools , it should have in the standard format which is type name description parameters etc.

write all the code in this current file and make sure it is in one file

The final input i want to give is a string which can be anything. the llm should get the query then it should decide which tool to call and then it should give me an answer.

For api keys i am using PYTHON-dotenv
and the command i was using was GROQ_API_KEY = os.getenv("GROQ_API_KEY")
