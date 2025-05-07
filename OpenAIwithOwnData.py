# Description: This script demonstrates how to use the OpenAI Python SDK to query a custom data source in Azure Search.
# The script takes a user input question and sends it to the Azure OpenAI API for completion.
# The completion request includes a data source configuration that specifies an Azure Search index to retrieve additional information.
# The script prints the response from the OpenAI API, which includes the answer to the question based on the data retrieved from Azure Search.
# You will need to set up an Azure Search service and index with the required data for this script to work.
# You will also need to set the following environment variables:
# - AZURE_OPENAI_ENDPOINT: The endpoint for the Azure OpenAI API
# - AZURE_OPENAI_KEY: The API key for the Azure OpenAI API
# - AZURE_OPENAI_DEPLOYMENT: The deployment name for the Azure OpenAI model
# - AZURE_SEARCH_SERVICE_ENDPOINT: The endpoint for the Azure Search service
# - AZURE_SEARCH_INDEX: The name of the Azure Search index to query
# - AZURE_SEARCH_ADMIN_KEY: The admin key for the Azure Search service

       
import os
import openai
import dotenv

dotenv.load_dotenv()
# Set up the OpenAI client with Azure credentials
# The endpoint, API key, and deployment name are read from environment variables
endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
api_key = os.environ.get("AZURE_OPENAI_KEY")
deployment = os.environ.get("AZURE_OAI_DEPLOYMENT")

# Create an instance of the Azure OpenAI client
client = openai.AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-02-01",
)



# Get user input question
text = input('\nEnter a question:\n')

# Send the question to the OpenAI API for completion
# The completion request includes a data source configuration for Azure Search
completion = client.chat.completions.create(
    model=deployment,
    messages=[
         {"role": "system", "content": "Provide a single answer limited to 200 characters."},
        {
            "role": "user",
            "content": text,
        },
    ],
    extra_body={
        "data_sources":[
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"],
                    "index_name": os.environ["AZURE_SEARCH_INDEX"],
                    "authentication": {
                        "type": "api_key",
                        "key": os.environ["AZURE_SEARCH_ADMIN_KEY"],
                    }
                }
            }
        ],
    }
)
# Print the response from the OpenAI API
print("\n" + completion.choices[0].message.content + "\n")
# print(completion.model_dump_json(indent=2))