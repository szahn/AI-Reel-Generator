# Social Media Reel Generator

Uses Python, OpenAI, Azure Video Indexer to generate short captioned reels from Youtube videos. Made with [Cursor](https://www.cursor.com).

## Firebase Database

Create a [Google Firebase account](https://firebase.google.com/) and download credentials for the database.Create a `firebase-credentials.json` in the the app root with connection to the Firebase database.

## Azure Setup

Create the following Azure resources:

* Resource Group
* Storage Account
* OpenAI Service
* Video Indexer
* Entra Id App Registration

## Setup Entra ID for Video Indexer API

Create an Entra App Registration. Then go to the subscription,  access control (IAM), role assignments, add role assignment. Select privileged administrator roles, contributor. Under members, select "User, group, or service principal", then click select members. Search for the app name and select.

## OpenAI API

* Get the OpenAI API Key from [OpenAI](https://platform.openai.com/)

## Replicate API

* Get a Replicate AI API Key from [replicate.com](https://replicate.com/)

## Environment Variables

Setup the `.env` with the following variables:

For more information on the Video Indexer API, see [Video Indexer Rest API](https://api-portal.videoindexer.ai/). You can get the video indexer account ID from [videoindexer.ai](https://videoindexer.ai).

Create a `.env` file with the following:

```
AzureStorageAccountName=''
AzureStorageContainerName=''
AzureStorageAccountContainerSasUrl=''
AzureVideoIndexerAccountName=''
AzureVideoIndexerResourceGroup=''
AzureVideoIndexerRegion=''
AzureVideoIndexerSubscriptionId=''
AzureVideoIndexerAccountId=''
AzureVideoIndexerAppTenantId=''
AzureVideoIndexerAppClientId=''
AzureVideoIndexerAppClientSecret=''
OpenAIAPIKey=''
ReplicateApiKey=''
```

## Run CLI

To run the generator from command-line, run:

```bash
python ./src/video-processor.py --videoUrl "YoutubeVideoUrl"
```

## Docker

To run the generator from Docker, run the following commands:

```
docker build -t video-processor .

docker run -v $(pwd)/videos:/app/videos -v $(pwd)/firebase-credentials.json:/app/firebase-credentials.json video-processor --videoUrl "Youtube_Video_Url"
```

## API

To run the API, run: `python run_api.py`


## Future Improvements

* Use semantic chunking (segment transcripts by context instead of timestamps) to improve summarization requests.
* Add React Material UI for processing, viewing, managing reels.
* Add Stripe payment processing for pay-per-reel.
* Make process asynchronous with queues to allow for batching of multiple reels.
* Improve processing time and costs with additional transcription services.