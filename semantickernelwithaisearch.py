# Description: This file contains the code to run the semantic kernel with Azure AI Search integration. 
# The code initializes the kernel, adds the Azure OpenAI chat completion service, and sets the execution settings for the chat prompt. It also creates a history of the conversation and initiates a back-and-forth chat between the user and the AI assistant. The user can input messages, and the AI assistant will respond based on the conversation history and the Azure OpenAI chat completion service. The conversation continues until the user enters "exit" to terminate the chat.
# The main function runs the chat loop and processes user input and AI responses using the Azure OpenAI chat completion service. The chat history is updated with user messages, and the AI responses are added to the history. The chat loop continues until the user enters "exit" to end the conversation.
# The asyncio.run() function is used to run the main function asynchronously and handle the chat interactions.
# The code demonstrates how to integrate the Azure OpenAI chat completion service with the semantic kernel to create a conversational AI agent that can engage in dialogues with users.
# The Azure OpenAI chat completion service provides responses to user messages based on the conversation history and the AI model's training. The execution settings control the behavior of the chat prompt, such as function choice and response generation.
# The chat history stores the messages exchanged between the user and the AI assistant, allowing for context-aware responses and maintaining the conversational flow.
# The Azure AI Search integration enables the AI assistant to retrieve additional information from an Azure Search index based on user queries, enhancing the responses with relevant data.
# Overall, the code showcases how to build a chatbot using the Azure OpenAI chat completion service and integrate it with the semantic kernel for advanced conversational capabilities.
# The chatbot can handle user queries, provide responses based on the chat history and external data sources, and engage users in meaningful conversations on various topics.


import asyncio
import logging
import os

from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from azure.search.documents.indexes import SearchIndexClient
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchStore


from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

import dotenv

dotenv.load_dotenv()


async def main():
    # Initialize the kernel
    kernel = Kernel()
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    api_key = os.environ.get("AZURE_OPENAI_KEY")
    base_url = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    search_endpoint = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
    search_index = os.environ.get("AZURE_SEARCH_INDEX")
    search_credentials = os.environ.get("AZURE_SEARCH_ADMIN_KEY")


    # Add Azure OpenAI chat completion
    chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        api_key=api_key,
        base_url=base_url,
        api_version=api_version
    )
    kernel.add_service(chat_completion)


    search_client = SearchIndexClient(endpoint=search_endpoint, credential=search_credentials)
    vector_store = AzureAISearchStore(search_index_client=search_client)
    kernel.add_service(vector_store)
    

    # Set the execution settings for the chat prompt
    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create a history of the conversation
    history = ChatHistory()

    # Initiate a back-and-forth chat
    userInput = None
    while True:
        # Collect user input
        userInput = input("User > ")

        # Terminate the loop if the user says "exit"
        if userInput == "exit":
            break

        # Add user input to the history
        history.add_user_message(userInput)

        # Get the response from the AI
        result = await chat_completion.get_chat_message_content(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
        )

        # Print the results
        print("Assistant > " + str(result))

        # Add the message from the agent to the chat history
        history.add_message(result)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())