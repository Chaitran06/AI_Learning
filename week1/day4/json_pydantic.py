import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("API key not found")

client=Groq(api_key=my_api_key)

model="llama-3.3-70b-versatile"
role="user"


#structure
from pydantic import BaseModel
class Ticket(BaseModel):
    name:str
    email:str
    issue:str

schema=Ticket.model_json_schema()
response_format={
    "type": "json_object"
}
system_prompt=f"""
Extract the personal information from the ticket strictly based on this schema and give me json output.
{schema}
"""
message_system={
    "role":"system",
    "content":system_prompt
}

text="Hello my name is Chaitran. I have purchased a samsung mobile which is not working at all. My address is hyderabad. My email is abc@gmail.com. My contact is 9347"
prompt=f""" 
This is a customer ticket. Please extract the personal information from this.
{text}
"""

# message: role and content
message={
    "role": role,
    "content": prompt
}
messages=[message_system,message]

response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)


answer=response.choices[0].message.content
print(answer)
