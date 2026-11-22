I want to make a multi agent system.
first i want to make a single agent system.
it will have one llm(groq)

it will have 2 tools, one is web search using tavily. you will find all api keys in env file
another will be a python calculator.

there will be one ask llm function, 
llm will decide which tools to use and how many times. 
there will be a  max attempts of 5.

then we will convert this to a multi agent system without langraph
in the multi agent there will be three ask llm functions.

first will be manager llm- its only job is to decide which helper llm to use.
second will be ask_search_llm which has access to only the search tool.
third will be the ask_math_llm which will have access to calculator tool.

role of each ask llm can be given by a system prompt
manager llm will also have a notes file where it will keep track of the responses by the helper llm.

finally we will have token usage in this also.
in the end we will compare both the systems and see which uses more tokens.
for test prepare a little complex query, which involves search and calculator maybe more than once.
of you have doubts then ask.