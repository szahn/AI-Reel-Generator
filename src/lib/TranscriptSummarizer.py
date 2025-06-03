from pprint import pprint
from pathlib import Path
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI

from .AzureBlobStorageClient import AzureBlobStorageClient
from .FirebaseDbHelper import FirebaseDbHelper
from .Config import Config

class TranscriptSummarizer:
    config = Config.from_env()

    openai_client = OpenAI(
        api_key=config.openai_apikey
    )

    blob_client = AzureBlobStorageClient(config)
    firebase = FirebaseDbHelper()

    def summarize_transcript(self, internalVideoId, firebaseId, transcriptFilename, summaryFilename):

        file = TranscriptSummarizer.openai_client.files.create(
            file=open(transcriptFilename, "rb"),
            purpose="assistants", # "user_data",
        )

        instructions = "You are summarizing a speech transcript"
        prompt_message = 'Quote 3-6 sections of the speech which are the best optimistic, factual, convincing ideas and concepts of the speech no longer than 60 seconds. Include the unmodified quote, relevant hash tags, short title and description summary of the quote in json format following this json template: ```json {quote: "", tags: [""], title: "", description: ""} ``` Do not change the original quote'

        assistant = TranscriptSummarizer.openai_client.beta.assistants.create(
            model="gpt-4o",
            instructions=instructions,
            name="Speech Transcription Editor",
            tools=[{"type": "file_search"}]
        )

        # Create a vector store
        vector_store = TranscriptSummarizer.openai_client.vector_stores.create(name="Transcripts")

        # Ready the files for upload to OpenAI
        #file_paths = ["edgar/goog-10k.pdf", "edgar/brka-10k.txt"]
        file_streams = [open(transcriptFilename,"rb")]

        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = TranscriptSummarizer.openai_client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )

        # You can print the status and the file counts of the batch to see the result of this operation.
        print(file_batch.status)
        print(file_batch.file_counts)

        assistant = TranscriptSummarizer.openai_client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

        thread = TranscriptSummarizer.openai_client.beta.threads.create(
            messages=[
                {
                "role": "user",
                "content": prompt_message,
                # Attach the new file to the message.
                "attachments": [
                    { "file_id": file.id, "tools": [{"type": "file_search"}] }
                ],            
                }
            ]
        )    

        print(thread.tool_resources.file_search)

        class SummaryEventHandler(AssistantEventHandler):


            @override
            def on_text_created(self, text) -> None:
                print(f"\nassistant > ", end="", flush=True)

            @override
            def on_tool_call_created(self, tool_call):
                print(f"\nassistant > {tool_call.type}\n", flush=True)

            @override
            def on_message_done(self, message) -> None:
                # print a citation to the file searched
                message_content = message.content[0].text
                annotations = message_content.annotations
                citations = []
                for index, annotation in enumerate(annotations):
                    message_content.value = message_content.value.replace(
                        annotation.text, f"[{index}]"
                    )
                    if file_citation := getattr(annotation, "file_citation", None):
                        cited_file = TranscriptSummarizer.openai_client.files.retrieve(file_citation.file_id)
                        citations.append(f"[{index}] {cited_file.filename}")

                summary = message_content.value
                print(summary)
                #print("\n".join(citations))

                if summaryFilename is not None and summaryFilename != "":
                    with open(summaryFilename, 'w') as resultsFile:
                        resultsFile.write(summary)

                    summaryBlobUrl = TranscriptSummarizer.blob_client.upload_blob(summaryFilename)

                if firebaseId is not None:
                    TranscriptSummarizer.firebase.save_summary(firebaseId, summaryFilename, summaryBlobUrl)

        with TranscriptSummarizer.openai_client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=instructions,
            event_handler=SummaryEventHandler(),
        ) as stream:
            stream.until_done()
            
