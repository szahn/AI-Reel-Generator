import pprint
import sys
from pytubefix import YouTube
from pytube.innertube import _default_clients
from pytube import cipher
import re
from datetime import datetime
import io
import os
import uuid
from azure.identity import DefaultAzureCredential #SharedTokenCacheCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier
import argparse
from dotenv import dotenv_values
import json
import subprocess

from .Consts import Consts
from .VideoIndexerClient import VideoIndexerClient
from .TranscriptParser import TranscriptParser
from .ReelGenerator import ReelGenerator
from .TranscriptSummarizer import TranscriptSummarizer
from .VideoDownloader import VideoDownloader
from .FirebaseDbHelper import FirebaseDbHelper
from .AzureBlobStorageClient import AzureBlobStorageClient
from .Config import Config
import uuid
from datetime import datetime

class VideoProcessor:
    """Handles the processing of videos including download, upload, and analysis."""

    def __init__(self, config:Config):
        self.config = config
        self.firebase = FirebaseDbHelper()

    def process_video(self, videoUrl):
        internalVideoId = self.generate_timestamped_guid()
        (videoFirebaseId, videoName, videoFilename, audioFilename) = self.download_video(internalVideoId, videoUrl)
        (videoDestUrl, audioDestUrl) = self.upload_video(internalVideoId, videoFirebaseId, videoFilename, audioFilename)
        (insightsFilename, transcriptFilename, summaryFilename) = self.index_video(internalVideoId, videoFirebaseId, audioDestUrl, videoName)
        self.parse_transcript(internalVideoId, videoFirebaseId, insightsFilename, transcriptFilename)
        self.summarize_transcript(internalVideoId, videoFirebaseId, transcriptFilename, summaryFilename)
        self.generate_reels(internalVideoId, videoFirebaseId, f"./videos/{internalVideoId}/{videoFilename}", transcriptFilename, summaryFilename)
        data = self.firebase.get_document(videoFirebaseId)

        return {
            "videoId": internalVideoId,
            "data": data
        }

    def generate_timestamped_guid(self):
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        unique_id = uuid.uuid4()
        return f"{timestamp}-{unique_id}"


    def upload_audio_video(self, internalVideoId, videoFirebaseId, videoFilename, audioFilename):
        AzureStorageAccountContainerSasUrl = self.config.azure_storage_container_sas_url
        container_client = ContainerClient.from_container_url(container_url=AzureStorageAccountContainerSasUrl)

        videoDestFilename = f"v{internalVideoId}.mp4"
        audioDestFilename = f"a{internalVideoId}.mp3"

        print("uploading {srcFilename} > {destFilename}".format(srcFilename=videoFilename, destFilename=videoDestFilename))
        print("uploading {srcFilename} > {destFilename}".format(srcFilename=audioFilename, destFilename=audioDestFilename))

        videoDestUrl = None
        audioDestUrl = None
        f = open(videoFilename, 'rb')
        try:
            video_blob_client = container_client.get_blob_client(blob=videoDestFilename)

            # Upload the blob data - default blob type is BlockBlob
            if (not video_blob_client.exists()):
                res = video_blob_client.upload_blob(f, blob_type="BlockBlob")
                print("uploaded file {blobUrl}".format(blobUrl=video_blob_client.url))
            else:
                print("file already exists")            

            videoDestUrl = video_blob_client.url
        finally:
            f.close()

        f = open(audioFilename, 'rb')
        try:
            # upload audio
            audio_blob_client = container_client.get_blob_client(blob=audioDestFilename)

            # Upload the blob data - default blob type is BlockBlob
            if (not audio_blob_client.exists()):
                res = audio_blob_client.upload_blob(f, blob_type="BlockBlob")
                print("uploaded file {blobUrl}".format(blobUrl=audio_blob_client.url))
            else:
                print("file already exists")            

            audioDestUrl = audio_blob_client.url

            firebase = FirebaseDbHelper()
            firebase.update_video_metadata(videoFirebaseId, videoDestUrl, audioDestUrl)
        finally:
            f.close()
            

        return (videoDestUrl, audioDestUrl)

    def index_video(self, internalVideoId, videoFirebaseId, videoUrl, videoName):
        print(f"INDEXING VIDEO {videoUrl}...")

        # create Video Indexer Client
        client = VideoIndexerClient(self.config)

        # Get access tokens (arm and Video Indexer account)
        client.authenticate_async()

        videoDescription = ""
        excludedAI = ["Faces", "ObservedPeople", "Celebrities", "KnownPeople", "Logos", "OCR", "RollingCredits", "DetectedObjects", "Clapperboard", "FeaturedClothing", "PeopleDetectedClothing"]
        videoId = client.upload_url_async(internalVideoId, videoName, videoUrl, excludedAI, False, videoDescription)
        
        print(f"Uploading video {videoId}...")

        client.wait_for_index_async(videoId)

        insights = client.get_video_async(videoId)

        insightsFilename = f"videos/{internalVideoId}/{internalVideoId}-insights.json"
        transcriptFilename = f"videos/{internalVideoId}/{internalVideoId}-transcript.json"
        summaryFilename = f"videos/{internalVideoId}/{internalVideoId}-summary.txt"

        with open(insightsFilename, 'w') as f:
            json.dump(insights, f)

        return (insightsFilename, transcriptFilename, summaryFilename)


    def download_video(self, internalVideoId, videoUrl):
        print(f"DOWNLOADING VIDEO {internalVideoId}...")
        videoDownloader = VideoDownloader(self.config)
        return videoDownloader.download_video(internalVideoId, videoUrl)

    def upload_video(self, internalVideoId, videoFirebaseId, videoFilename, audioFilename):
        print(f"UPLOADING AUDIO AND VIDEO {internalVideoId}...")
        return self.upload_audio_video(internalVideoId, videoFirebaseId, f"./videos/{internalVideoId}/{videoFilename}", f"./videos/{internalVideoId}/{audioFilename}")

    def parse_transcript(self, internalVideoId, videoFirebaseId, insightsFilename, transcriptFilename):
        print(f"PARSING TRANSCRIPT {internalVideoId}...")
        transcriptParser = TranscriptParser(self.config)
        transcriptParser.parse_transcript(internalVideoId, videoFirebaseId, insightsFilename, transcriptFilename)

    def summarize_transcript(self, internalVideoId, videoFirebaseId, transcriptFilename, summaryFilename):
        print(f"SUMMARIZING TRANSCRIPT {internalVideoId}...")
        transcriptSummarizer = TranscriptSummarizer()
        transcriptSummarizer.summarize_transcript(internalVideoId, videoFirebaseId, transcriptFilename, summaryFilename)

    def generate_reels(self, internalVideoId, videoFirebaseId, videoFilename, transcriptFilename, summaryFilename):
        print(f"GENERATING REELS {internalVideoId}...")
        reelGenerator = ReelGenerator(self.config)
        reelGenerator.generate_reels(internalVideoId, videoFirebaseId, videoFilename, transcriptFilename, summaryFilename)
