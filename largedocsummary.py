# Description: This script reads a PDF file and extracts the text from it. 
# The text is then split into chunks 
# sent to the Azure Text Analytics service for abstractive summarization. 
# The script combines the summaries from all chunks into a single summary and saves it to a file.
# You will need an Azure Language Service created with the key
# and endpoint in the environment variables AZURE_LANGUAGE_KEY and AZURE_LANGUAGE_ENDPOINT.



import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from pypdf import PdfReader
import dotenv

dotenv.load_dotenv()

def create_chunks(text, chunk_size=10000, overlap=2000):  # 800KB chunks with 200 char overlap
    print("Creating chunks...")
    chunks = []
    start = 0
    text_length = len(text)
    print(f"Text length: {text_length}")
    
    while start < text_length:
        print(f"Starting new chunk at position {start}")
        end = start + chunk_size
        print(f"Initial end position: {end}")
        
        # If this is not the last chunk, adjust end to not break words
        if end < text_length:
            # Adjust end to the last space within the chunk
            original_end = end
            while end > start and not text[end-1].isspace():
                end -= 1
            print(f"Adjusted end from {original_end} to {end} to avoid breaking words")
        else:
            end = text_length
            print(f"Last chunk, using text_length as end: {end}")
            
        # Create chunk and add to list
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            # Store chunk as plain string, not in a list
            chunks.append(chunk)
            print(f"Added chunk of length: {len(chunk)}")
            
        # Move start position for next chunk, including overlap
        old_start = start
        start = end - overlap
        print(f"Moving start position from {old_start} to {start} (overlap: {overlap})")
        
        if start <= old_start:
            print("Warning: Start position not advancing!")
            # Force advancement to avoid infinite loop
            start = end
            print(f"Forced start position to {start}")
    
    print(f"Final number of chunks: {len(chunks)}")
    return chunks


endpoint = os.environ["AZURE_LANGUAGE_ENDPOINT"] 
key = os.environ["AZURE_LANGUAGE_KEY"] 

text_analytics_client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))

# First, combine all pages into a single string
reader = PdfReader("ENTER PATH TO PDF FILE")
# read the full pdf file
number_of_pages = len(reader.pages)
print(f"Found {number_of_pages} pages in PDF")

full_text = ""
pagenumber = 1
for page in reader.pages:

    # print(f"Processing page {pagenumber}")
    page_text = page.extract_text()
    if page_text:
        full_text += page_text + " "
    pagenumber += 1

print("about to chunk")
# Then create chunks from the combined text
chunks = create_chunks(full_text)
print(f"Created {len(chunks)} chunks")
for chunk in chunks:
    print(f"Chunk length: {len(chunk)}")
    # print(chunk)


all_summaries = []

for chunk in chunks:
    # Properly format the documents for the API
    documents = [chunk]
    # print(chunk)
    try:
        poller = text_analytics_client.begin_abstract_summary(documents)


        actions_results = poller.result()
        for action_result in actions_results:
            if action_result.kind == "AbstractiveSummarization":
                for summary in action_result.summaries:
                    all_summaries.append(summary.text)
                #print("Summaries extracted:")
                #[print(f"{summary.text}\n") for summary in action_result.summaries]
            elif action_result.is_error is True:
                print("...Is an error with code '{}' and message '{}'".format(
                    action_result.error.code, action_result.error.message
                ))
    except Exception as e:
        print(f"Error processing chunk: {str(e)}")

combined_summary = "".join(all_summaries)
print("\nCOMBINED SUMMARY OF ALL CHUNKS:")
print("================================")
print(combined_summary)

documents=[combined_summary]
poller = text_analytics_client.begin_abstract_summary(documents, sentence_count=10)
abstract_summary_results = poller.result()
for result in abstract_summary_results:
    if result.kind == "AbstractiveSummarization":
        print("final summary of summary:")
        # save the summary to a file
        
        with open("final_summary.txt", "w", encoding="utf-8") as f:
            for summary in result.summaries:
                f.write(f"{summary.text}\n")
        [print(f"{summary.text}\n") for summary in result.summaries]
    elif result.is_error is True:
        print("...Is an error with code '{}' and message '{}'".format(
            result.error.code, result.error.message
        ))




with open("combined_summary.txt", "w", encoding="utf-8") as f:
    f.write(combined_summary)
print("\nSummary has been saved to 'combined_summary.txt'")
