I am building a restuarant order management system using langgraph.
i will explain you very clearly what i want and what is the architecture, i wll also explain you the nodes, edges and the state.
in the end i will give you test cases to simulate and to tell me whether they pass or not.

The rough plan is:
There will be a user, when the code runs the user will give and order, this will be taken as an input which i will type. This order should go to the llm. the order as of now should contain the dish and the required quantity.
For simplicity purpose, for now we will limit the order to one particular dish and whatever quantity the user wants.
The llm will have to extract the order name and the quantity from the user input.
if the user input is unrealted to food odering the llm should not process that and tell the user that  it is not a general purpose llm, it is a food ordering llm
Once the llm has order dish and quantuty it will send that to a node caLLED order_confirm The rtask of this order conform is to look at the menu (i will tell ypu the menu later in this prompt). The\n this node will decide one of 3 case the order is available the order is partially available m,eans quantuty is not suficient the order is not available at all (dish being not i the menu or 0 quantity avilable) it will put this in the status of the state (I will tell u the exact content of the langraph state as well)

Once the llm recievedd this if the status is confiormed (full available) it should call another node called cook. if the staus is partail or not available it should again prompt the user to decide the user can either place a new order or can cionform if he wants to go ahead with the3 partial order
This order reties will be limited to 3 attempts menaing if after 3 attempt the user is not satisfied the system will come the the END node
Now when the cook node is called there can be 2 cases either the cook is done then the status will be Ready and if the cook fails( we can use a prob function). give 40% chanes of fail and 60 % chance of success

if the cook fails there shgould be 1 more attempt allowed for cook to suceed. if the cook fails even after these then the llm should issue a aplogy to the user and come to END state

if the cook suceeds, the status will be REAADY and the next node will be called which is serve simialr to cook this also has 2 cases servre pass or serve fail this also has 2 retry attempt if the serve fails 2 times then the llm should issue a aplogy to the user and come to END state

if the serve suceeds the status should become complete the llm should issue a message to the user saying your oder is complete if serve fails then cook should be called one more time to retruy. Note that if cook has exhausted its retry attempts then it should not cook again and llm should issue an apology and come to end state.

Now the state of langragph
there should be a annotated message be llm and user.

there should be order details dish name as str required quantuty as int available quantity as string order_confirm will write the available quantuty by readibng the menu the llm should get to know the order confrm status by reading the state if a dish is not avilabel in the mnu then orderconfirm should write 0 as avail quantity

then there should be status each node will update the status as specifed in the above rules then order retry attemps which are 3 
cook retry attemnpts which are 2 
serve retry attempts which are 2 
each time a filure haappend and a node is retrying it should diecreent the couner if any retry counter becomes 0 it means it is over. 
llm shoukd understand whether it has to give a retry or issue apology by reading this counter in the end thre should be final result whehter the orede was completed or not.


Write the code and ask if there are any open questions from your side then ask i will give you some test scenaiors to test later on

TC1 a user ask a unrealted question then he palces a order which is partial then he rejects the partial and wants to order again again he ordes a dish which is not avilabl expected. END due to order retry

TC2 user places a order which can be availeble cook makes it fails once cooks again cucess serve fails once cook retries success serve does success overall success

TC3 user orders partal doesn not want partial orders again fuylly available cooks kakes it fails makes again success serve fails cook retries success serve fails again cook does not retry ue to cook retru exhaist overall FAIl