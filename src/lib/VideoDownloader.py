import sys
import argparse
from pytubefix import YouTube
from pytube.innertube import _default_clients
from pytube import cipher
import re
import firebase_admin
from firebase_admin import credentials, firestore
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
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os

from .AzureBlobStorageClient import AzureBlobStorageClient
from .FirebaseDbHelper import FirebaseDbHelper
from .Config import Config


class VideoDownloader:

    def __init__(self, config : Config):
        self.upload_client = AzureBlobStorageClient(config)
        self.firebase = FirebaseDbHelper()

    def sanitize_filename(self, filename):
        return re.sub(r'[^a-zA-Z0-9]', '-', filename)

    def convert_mp4_to_mp3(self, input_file, output_file=None):
        """
        Convert an MP4 file to MP3 using ffmpeg.
        
        Args:
            input_file (str): Path to the input MP4 file
            output_file (str, optional): Path to the output MP3 file. If not provided,
                                    will use the same name as input with .mp3 extension
        
        Returns:
            str: Path to the output MP3 file
        """

        print(f"Converting video {input_file} to audio {output_file}")

        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.mp3'
        
        try:
            # Construct the ffmpeg command
            command = [
                'ffmpeg',
                '-i', input_file,  # Input file
                '-vn',  # No video
                '-acodec', 'libmp3lame',  # Use MP3 codec
                '-q:a', '2',  # Audio quality (2 is high quality, range is 0-9)
                '-y',  # Overwrite output file if it exists
                output_file
            ]
            
            # Run the command
            subprocess.run(command, check=True, capture_output=True)
            print(f"Successfully converted {input_file} to {output_file}")
            return output_file
        
        except subprocess.CalledProcessError as e:
            print(f"Error converting file: {str(e)}")
            print(f"ffmpeg stderr: {e.stderr.decode()}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None


    def download_video(self, internalVideoId, videoUrl):
        print("downloading video '{videoUrl}'".format(videoUrl=videoUrl))

        yt = YouTube(videoUrl)
        print(f"ID: {internalVideoId}")
        print("Title: {title}".format(title=yt.title))
        print("Published: {publishDate}".format(publishDate=yt.publish_date))
        print("Author: {author}".format(author=yt.author))
        print("Keywords: {keywords}".format(keywords=yt.keywords))

        stream = yt.streams.filter(progressive=True, mime_type="video/mp4").order_by('resolution').asc().first()
        print("downloading stream {streamId}".format(streamId=stream.itag))

        os.makedirs(f"./videos/{internalVideoId}", exist_ok=True)

        videoName = self.sanitize_filename(yt.title).replace("--", "-").lower()
        videoFilename = f"{internalVideoId}.mp4"
        videoThumbnailFilename = f"videos/{internalVideoId}/{internalVideoId}-thumb.jpg"
        audioFilename = f"{internalVideoId}.mp3"

        print (f"downloading {videoFilename}")

        stream.download(output_path=f"videos/{internalVideoId}", filename=videoFilename)

        clip = VideoFileClip(f"./videos/{internalVideoId}/{videoFilename}")
        clip.save_frame(videoThumbnailFilename, t=3)  # Save frame at 3 sec
        videoThumbnailBlobUrl = self.upload_client.upload_blob(videoThumbnailFilename)

        self.convert_mp4_to_mp3(f"videos/{internalVideoId}/{videoFilename}".format(filename=videoFilename), f"videos/{internalVideoId}/{audioFilename}".format(filename=audioFilename))

        # Store video metadata in Firestore
        video_data = {
            'internalId': internalVideoId,
            'title': yt.title,
            'name': videoName,
            'description': '', #yt.description,
            'author': yt.author,
            'publish_date': yt.publish_date,
            'keywords': yt.keywords,
            'key_moments': yt.key_moments,
            'video_source_url': videoUrl,
            'videoFilename': videoFilename,
            'audioFilename': audioFilename,
            'video_thumbnail_filename': videoThumbnailFilename,
            'video_thumbnail_blob_url': videoThumbnailBlobUrl
        }

        videoFirebaseId = self.firebase.store_video_metadata(video_data)

        return (videoFirebaseId, videoName, videoFilename, audioFilename)
