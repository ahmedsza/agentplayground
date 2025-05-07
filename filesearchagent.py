# Description: This script demonstrates how to create a File Search Agent in Azure AI Foundry.
# The agent will summarize a Request For Proposal (RFP) in the knowledge store based on a template provided in the instructions.
# The agent will use a File Search Tool to search for the RFP file in the knowledge store.
# The agent will generate a summary of the RFP based on the template provided in the instructions.
# The agent will create a thread, send a message to generate the summary, and create a run to process the message.
# The agent will delete the vector store and the agent after processing the message.
# The script will print the text messages from the agent in the thread.


import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, MessageAttachment, FilePurpose
from azure.identity import DefaultAzureCredential
import dotenv

dotenv.load_dotenv()

# Create an Azure AI Client from a connection string, copied from your Azure AI Foundry project.
# At the moment, it should be in the format "<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<ProjectName>"
# Customer needs to login to Azure subscription via Azure CLI and set the environment variables

credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    credential=credential, conn_str=os.environ["PROJECT_CONNECTION_STRING"] 
)

# We will upload the local file and will use it for vector store creation.

#upload a file
file_path = 'ENTER PATH TO FILE'
file = project_client.agents.upload_file_and_poll(file_path=file_path, purpose=FilePurpose.AGENTS)
print(f"Uploaded file, file ID: {file.id}")

# create a vector store with the file you uploaded
vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="my_vectorstore")
print(f"Created vector store, vector store ID: {vector_store.id}")

# create a file search tool
file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])

agent_instruction='''
Summarize the Request For Proposal (RFP) in the knowledge store based on this template:
 
Requestor: [Company Name Producing the RFP],
Project Title: [Title],
Deadline: [Date of time to submit the proposal by],
Project Overview: [Overview],
Scope of Work: [5-10 Scope of Work items],
Deliverables: [5-10 Deliverables items],
Timeline: [Timeline],
Budget: [Budget of the project. If no budget, then none],
Keywords: [Keywords],
Technical Requirements: [Specific features, functionalities, and standards we must meet for the RFP proposed solutions - list of items],
Clarifying Questions: [5-10 Questions that are unclear from the RFP to better create proposal - list of items],
Contact Information: [Contact]
Summary: [A comprehennsive summary of the RFP ]
 
Avoid using double-quotes in the within values that are plain text, of each key. For single words, use double-quotes. But for sentences, in a replace any double quotes by single quotes. Just use single quotes. Example: adasd "FOO" asdasd should be adasd 'FOO' asdasd.
 
Generate a json like reponse strictly using the keys from the template. Remove the ```json ``` headers and footers, and in the order they were placed
 
Please extract the relevant information from the RFP and fill in the template. Do not include any introductory phrases or summaries like Okay, here's the summary or this is a summary.
 
Do not use non-ascii characters.
'''

# notices that FileSearchTool as tool and tool_resources must be added or the agent will be unable to search the file
agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="my-summarizer-agent",
    instructions=agent_instruction,
    tools=file_search_tool.definitions,
    tool_resources=file_search_tool.resources,
)
print(f"Created agent, agent ID: {agent.id}")

# Create a thread
thread = project_client.agents.create_thread()
print(f"Created thread, thread ID: {thread.id}")


message = project_client.agents.create_message(
    thread_id=thread.id, role="user", content="Generate summary"
)
print(f"Created message, message ID: {message.id}")

run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
print(f"Created run, run ID: {run.id}")

project_client.agents.delete_vector_store(vector_store.id)
print("Deleted vector store")

project_client.agents.delete_agent(agent.id)
print("Deleted agent")

messages = project_client.agents.list_messages(thread_id=thread.id)

for text_message in messages.text_messages:
    print(text_message.as_dict())
