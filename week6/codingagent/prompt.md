We want to make a coding agent in python which can solve simple bugs.
We will use the groq llm for this, check past files for the model and we will use them.
The llm will have some tools which will help in solving the bug.

One tool can be search files which lists path of files which are related to the bug as per the llm.
we need search in file tool which can give line numbers related to the bug.
Other tool needed is replace which allows the replacing a line with another line.
To test this, I want to test this myself. Prepare a simple .cpp file and write boilerplate code in it. Donot introduce any bug now, i will introduce and test it myself.

I want to give the bug in simple english in cli and the llm and the tools should solve it.
make the system without langraph and keep it simple.
Also there will be max retry of 3 times. If the llm cannot solve the bug inside this this limit, it should print a message saying "Cannot solve the bug"

There should be also clear print statements saying which tool was called at each step, we want to understand the flow completely. 
as soon as i change the cpp file and run the agent, it should ask me my bug, after i give my bug it should begin with solving it.

Donot write any test cases for now.
if anything is unclear, ask me

