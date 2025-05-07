# Description: This script is used to create an Azure Search index, datasource, skillset, and indexer to index PDF documents stored in an Azure Blob Storage container.
# The script uses the Azure SDK for Python to interact with Azure Search and Blob Storage services.
# The Azure Search index is configured with a custom skillset that leverages the Azure Cognitive Search built-in skills for text extraction and language detection.
# The datasource is set up to connect to the Azure Blob Storage container containing the PDF documents for indexing.
# The skillset includes the built-in skills for text extraction and language detection, as well as custom skills for entity recognition and key phrase extraction.
# The indexer is created to synchronize the data from the datasource to the search index using the configured skillset for document processing.
# The script demonstrates how to set up the necessary resources in Azure Search to index PDF documents from Azure Blob Storage and extract insights using cognitive skills.
# The Azure Cognitive Search service enables full-text search and advanced text processing capabilities on structured and unstructured data sources.
# The script can be extended to include additional custom skills and enrichments based on the specific requirements of the document processing pipeline.
# The Azure SDK for Python provides a convenient way to interact with Azure services and manage the search index, datasource, skillset, and indexer configurations.
# The script can be run as a standalone program or integrated into a larger data processing workflow to automate document indexing and analysis tasks.
# The Azure Search service offers scalable and reliable document indexing capabilities for building search applications and knowledge discovery solutions.


from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
import os
from azure.storage.blob import BlobServiceClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from lib.common import (
    create_search_index,
    create_search_datasource, 
    create_search_skillset,
    create_search_indexer,
    get_chunks,
    get_token_length,
    plot_chunk_histogram
)
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

search_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
search_index = os.environ["AZURE_SEARCH_INDEX"]
search_datasource = os.environ["AZURE_SEARCH_DATASOURCE"] 
search_skillset = os.environ["AZURE_SEARCH_SKILLSET"]
search_indexer = os.environ["AZURE_SEARCH_INDEXER"]
azure_openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
azure_openai_embedding_deployment_id = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ID"]
blob_container = os.environ["AZURE_BLOB_CONTAINER"]
blob_connection_string = os.environ["AZURE_BLOB_CONNECTION_STRING"]
blob_account_url = os.environ["AZURE_BLOB_ACCOUNT_URL"]

search_credential = AzureKeyCredential(os.environ["AZURE_SEARCH_ADMIN_KEY"]) if len(os.environ["AZURE_SEARCH_ADMIN_KEY"]) > 0 else DefaultAzureCredential()
azure_openai_key = os.environ["AZURE_OPENAI_KEY"] if len(os.environ["AZURE_OPENAI_KEY"]) > 0 else None

def open_blob_client():
    if not blob_connection_string.startswith("ResourceId"):
        print("Using connection string")
        return BlobServiceClient.from_connection_string(
            blob_connection_string,
            max_block_size=1024*1024*8,
            max_single_put_size=1024*1024*8
        )
    return BlobServiceClient(
        account_url=blob_account_url,
        credential=blob_connection_string,
        max_block_size=1024*1024*8,
        max_single_put_size=1024*1024*8
    )

def upload_pdf():
    blob_client = open_blob_client()
    print(blob_client)
    container_client = blob_client.get_container_client(blob_container)
    print(container_client)
    if not container_client.exists():
        container_client.create_container()
        
    file_path = os.path.join("earth_at_night_508.pdf")
    blob_name = os.path.basename(file_path)
    blob_client = container_client.get_blob_client(blob_name)
    if not blob_client.exists():
        with open(file_path, "rb") as f:
            blob_client.upload_blob(data=f, overwrite=True)

def setup_search_resources():
    search_index_client = SearchIndexClient(endpoint=search_endpoint, credential=search_credential)
    index = create_search_index(
        search_index,
        azure_openai_endpoint,
        azure_openai_embedding_deployment_id,
        azure_openai_key
    )
    search_index_client.create_or_update_index(index)
    
    search_indexer_client = SearchIndexerClient(endpoint=search_endpoint, credential=search_credential)
    
    data_source = create_search_datasource(
        search_datasource,
        blob_connection_string,
        blob_container
    )
    search_indexer_client.create_or_update_data_source_connection(data_source)
    
    skillset = create_search_skillset(
        search_skillset,
        search_index,
        azure_openai_endpoint,
        azure_openai_embedding_deployment_id,
        azure_openai_key,
        text_split_mode='pages',
        maximum_page_length=2000,
        page_overlap_length=500
    )
    search_indexer_client.create_or_update_skillset(skillset)
    
    indexer = create_search_indexer(
        indexer_name=search_indexer,
        index_name=search_index,
        datasource_name=search_datasource,
        skillset_name=search_skillset
    )
    search_indexer_client.create_or_update_indexer(indexer)
    search_indexer_client.run_indexer(search_indexer)
    
    print("Running indexer")


def main():
    # Upload PDF file to Azure Blob Storage
    # recommend commenting out this line after the first run to avoid re-uploading the same file
    upload_pdf()
    # Setup Azure Search resources including indexer 
    # only needs to be run once to create the resources
    # recommend running upload_pdf first by itself, the commenting it out, and run below line separately
    # after running check in azure that blob storage created and search index created
    setup_search_resources()

if __name__ == "__main__":
    main()