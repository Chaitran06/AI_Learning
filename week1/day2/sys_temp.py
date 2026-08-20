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
prompt="Suggest a name for my clothing company"

# message: role and content
message={
    "role": role,
    "content": prompt
}
message_system={
    "role":"system",
    "content":"You are a brand manager who suggests name for my company, suggest one name only."
}
messages=[message_system, message]
#temp by default is 0-> meaning safe answer. Range is{0,2}

response=client.chat.completions.create(model=model, messages=messages, temperature=2)

#print(response)

#print("#######################################")

answer=response.choices[0].message.content
print(answer)
