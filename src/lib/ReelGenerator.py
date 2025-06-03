import json
import os
import argparse
from pprint import pprint
import re
import string
import ffmpeg
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from dotenv import dotenv_values

from .AzureBlobStorageClient import AzureBlobStorageClient
from .ReplicateAIClient import ReplicateAIClient
from .FirebaseDbHelper import FirebaseDbHelper
from .Config import Config

# Regular expression to capture each quote block
patterns = re.compile(
    r'\*\*Quote:\*\*\s*"(?P<quote>.*?)"\s*'
    r'\*\*Tags:\*\*\s*`(?P<tags>.*?)`\s*'
    r'\*\*Title:\*\*\s*"(?P<title>.*?)"\s*'
    r'\*\*Description:\*\*\s*(?P<description>.*?)(?=\n\d+\.|\Z)', 
    re.DOTALL | re.IGNORECASE
)

class ReelGenerator:

    def __init__(self, config:Config):
        self.blob_client = AzureBlobStorageClient(config)
        self.replicate_client = ReplicateAIClient(config)
        self.firebase = FirebaseDbHelper()

    def detect_json_type(self, json_string):
        try:
            parsed = json.loads(json_string)
            if isinstance(parsed, dict):
                return (parsed, "object")
            elif isinstance(parsed, list):
                return (parsed, "array")
            else:
                return (None, f"other ({type(parsed).__name__})")
        except json.JSONDecodeError:
            return (None, "invalid JSON")

    def read_summary(summaryFilename):
        with open(summaryFilename, 'r') as file:
            return file.read()
        
    def try_extract_raw_quoted_text(filename):
        data = None
        with open(filename, 'r') as file:
            data = file.read()


        idx = 0

        entries = []
        while (idx >= 0):
            quote_token = '**Quote:**'
            idx = data.find(quote_token, idx)
            if idx == -1:
                break
            start_quote_idx = data.find('"', idx + len(quote_token))
            if (start_quote_idx == -1):
                break
            end_quote_idx = data.find('"', start_quote_idx+1)
            quote = data[start_quote_idx+1:end_quote_idx].strip()
            idx = end_quote_idx+1

            tags_token = '**Tags:**'
            tags_idx = data.find(tags_token, idx)
            if tags_idx > -1:              
                tags_idx = data.find("[", tags_idx)
                if tags_idx > -1:
                    end_tags_idx = data.find(']', tags_idx+1)
                    tags = data[tags_idx+1:end_tags_idx-1].replace('"', '').strip()
                    tags = tags.split(',')
                    tags = [tag.strip() for tag in tags]
                idx = end_tags_idx+1
            else:
                tags = []


            title_token = '**Title:**'
            title_idx = data.find(title_token, idx)
            if title_idx > -1:
                title_idx = data.find('"', title_idx+len(title_token))
                if title_idx > -1:
                    end_title_idx = data.find('"', title_idx+1)
                    title = data[title_idx+1:end_title_idx].strip()
                idx = title_idx + 1
            else:
                title = ''

            entries.append({
                'quote': quote,
                'tags': tags,
                'title': title,
                'description': ''
            })


    def try_read_and_match_json_lines(self, filename):

        results = []

        summary_content = None
        with open(filename, 'r') as file:
            summary_content = file.read()

        results = []

        def get_non_json_matches(data):
            for match in patterns.finditer(data):
                entry = {
                    'quote': match.group('quote').strip(),
                    'tags': [tag.strip() for tag in match.group('tags').split('`, `')],
                    'title': match.group('title').strip(),
                    'description': match.group('description').strip().rstrip('.')
                }
                results.append(entry)

        json_pattern = r'(?<=```json\s).*?\s.*?(?=```)'
        json_match = re.findall(json_pattern, summary_content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if json_match:
            print(f"Found {len(json_match)} JSON blocks in summary")
            for i, group in enumerate(json_match):
                (json_result, json_type) = self.detect_json_type(group)

                if json_type == "array":
                    for item in json_result:
                        results.append(item)
                elif json_type == "object":
                    results.append(json_result)
        else:
            get_non_json_matches(summary_content)

        return results


    def sanitize_text(self, text):
        sanitized = re.sub(r'[^\w\s]', ' ', text)
        return re.sub(r'\s{2,}', ' ', sanitized).lower().strip()
    
    def rebuild_transcript_text(self, transcriptFilename):
        transcriptJson = None
        with open(transcriptFilename, 'r') as f:
            transcriptJson = json.load(f)

        transcriptText = ""
        transcriptSlices = []

        pos = 0
        for transcriptItem in transcriptJson:
            text = self.sanitize_text(transcriptItem['text'].lower())
            transcriptText += text
            
            sliceData = {
                'pos': pos,
                'text': text,
                'start': transcriptItem['start'],
                'end': transcriptItem['end']
            }

            transcriptSlices.append(sliceData)
            pos += len(text)

        sanitizedTranscriptText = transcriptText

        return (sanitizedTranscriptText, transcriptSlices)

    def extract_reels(self, internalVideoId, transcriptFilename, summaryFilename):
        reels = []

        transcriptJson = None
        with open(transcriptFilename, 'r') as f:
            transcriptJson = json.load(f)

        entries = self.try_read_and_match_json_lines(summaryFilename)
        
        if len(entries) == 0:
            entries = self.try_extract_raw_quoted_text(summaryFilename)

        (transcriptText, transcriptSlices) = self.rebuild_transcript_text(transcriptFilename)

        for entry in entries:
            entryQuoteText = entry['quote']
            if entryQuoteText.find('...') != -1:
                entryQuoteText = entryQuoteText.split('...')[0]
            entryQuote = self.sanitize_text(entryQuoteText)

            quoteStartPos = transcriptText.find(entryQuote)
            quoteEndPos = quoteStartPos + len(entryQuote)
            if quoteStartPos == -1:
                continue
            else:
                entry['index'] = quoteStartPos


            matchFound = False
            for pos in range(len(transcriptSlices)):
                slice = transcriptSlices[pos]
                if slice['pos'] >= quoteStartPos:
                    entry['start'] = slice['start']
                    entry['end'] = slice['end']
                    entry['text'] = slice['text']
                    matchFound = True
                    break
            
            if not matchFound:
                slice = transcriptSlices[len(transcriptSlices) -1]
                entry['start'] = slice['start']
                entry['end'] = slice['end']
                entry['text'] = slice['text']
                matchFound = True

        reelIndex = 0
        startTimes = []

        for entry in entries:
            try:
                if 'start' not in entry or 'end' not in entry:
                    continue

                if (entry['start'] == None or entry['end'] == None or entry['text'] == None):
                    continue

                if entry['start'] in startTimes:
                    continue

                startTime = entry['start']
                startTimes.append(startTime)

                endTime = entry['end']

                videoDestFilename = f"./videos/{internalVideoId}/{internalVideoId}-reel-{reelIndex}.mp4"
                videoDestThumbnailFilename = f"./videos/{internalVideoId}/{internalVideoId}-{reelIndex}.jpg"
                videoDestReelCaptionedFilename = f"./videos/{internalVideoId}/{internalVideoId}-reel-{reelIndex}-captioned.mp4"
                videoDestBlobname = f"v{internalVideoId}-reel-{reelIndex}.mp4"

                reelIndex+=1

                try:
                    print(f"Reel {reelIndex} from {startTime} to {endTime}: {videoDestFilename}")

                    entry['reel_filename'] = videoDestFilename
                    entry['reel_thumbnail_filename'] = videoDestThumbnailFilename
                    entry['reel_captioned_filename'] = videoDestReelCaptionedFilename
                    entry['reel_blobname'] = videoDestBlobname
                    del entry['text']
                    
                    reels.append(entry)
                    
                except Exception as e:
                    print(f"Error generating reel {reelIndex}: {e}")
                    continue
            except Exception as e:
                print(f"Error generating reel {reelIndex}: {e}")
                continue

        return reels


    def generate_reels(self, internalVideoId, firebaseId, videoFilename, transcriptFilename, summaryFilename):

        reels = self.extract_reels(internalVideoId, transcriptFilename, summaryFilename)
        reel_count = len(reels)

        print(f"Found {reel_count} reels...")

        for reelIndex in range(reel_count):

            try:
                reel = reels[reelIndex]
                startTime = reel['start']
                endTime = reel['end']
                videoDestFilename = reel['reel_filename']
                videoDestThumbnailFilename = reel['reel_thumbnail_filename']
                videoDestReelCaptionedFilename = reel['reel_captioned_filename']
                videoDestBlobname = reel['reel_blobname']

                print(f"Generating reel {reelIndex} from {startTime} to {endTime}: {videoFilename} > {videoDestFilename}")

                clip = (VideoFileClip(videoFilename).subclipped(startTime, endTime))
                clip.write_videofile(videoDestFilename)
                clip.save_frame(videoDestThumbnailFilename, t=0)  # Save frame at 1 sec

                print(f"Generated {videoDestFilename}")

                print(f"Uploading reel {reelIndex}  {videoDestBlobname}")
                blobUrl = self.blob_client.upload_blob(videoDestFilename) #) videoDestBlobname)
                thumbnailBlobUrl = self.blob_client.upload_blob(videoDestThumbnailFilename) #) videoDestBlobname)

                reel['reel_url'] = blobUrl
                reel['reel_thumbnail_filename'] = videoDestThumbnailFilename
                reel['reel_thumbnail_url'] = thumbnailBlobUrl
                print(f"Uploaded {blobUrl}")

                print(f"Captioning reel {reelIndex}  {videoDestReelCaptionedFilename}")

                # Generate captions
                self.replicate_client.tiktok_captions(internalVideoId, blobUrl, videoDestReelCaptionedFilename)
                captionedBlobUrl = self.blob_client.upload_blob(videoDestReelCaptionedFilename)
                reel['reel_captioned_filename'] = videoDestReelCaptionedFilename
                reel['reel_captioned_url'] = captionedBlobUrl
                print(f"Uploaded {captionedBlobUrl}")

                if 'text' in reel:
                    del reel['text']
                
            except Exception as e:
                print(f"Error generating reel {reelIndex} from {videoFilename}: {e}")
                continue

        self.firebase.save_reels(firebaseId, reels)
