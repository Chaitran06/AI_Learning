import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("API key not found")

client=Groq(api_key=my_api_key)

model="openai/gpt-oss-120b"


#step1- create knowledge base
knowledge_base={
    "age":"The age of chaitran is 23 years",
    "net worth":"The net worth of chaitran is 10000000"
}

#step2- retreival dictonary(pdf, doc, can also be used)
def retrieve_info(question):
    question=question.lower()
    if "age" in question:
        return knowledge_base["age"]
    elif "net worth" in question:
        return knowledge_base["net worth"]
    else:
        return None
  
def ask_llm(question):
    context=retrieve_info(question)

    sys_prompt=f"""answer in only one line. And answer only based on this context, do not hallucinate. Context:{context}"""
    system_message={
        "role":"system",
        "content":sys_prompt
    }
    message={
        "role":"user",
        "content":question

    }
    messages=[system_message,message]
    response=client.chat.completions.create(model=model, messages=messages)
    answer=response.choices[0].message.content
    return answer

question="how old is chaitran"
print(ask_llm(question))
# this is very rigid software. it matches word by word and gives answer.
