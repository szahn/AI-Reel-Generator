from pprint import pprint
import json
import io
import os
from datetime import datetime

from .AzureBlobStorageClient import AzureBlobStorageClient
from .FirebaseDbHelper import FirebaseDbHelper
from .Config import Config

TranscriptSectionDurationSeconds = 60 

class TranscriptParser:

    def __init__(self, config:Config):
        self.upload_client = AzureBlobStorageClient(config)
        self.firebase = FirebaseDbHelper()

    def parse_transcript(self, internalVideoId, videoFirebaseId, videoJsonFilename, transcriptFilename):
        _, file_extension = os.path.splitext(transcriptFilename)
        isJsonL = file_extension == ".jsonl"

        transcript = []
        
        with open(videoJsonFilename) as f:
            json_data = json.load(f)

            videos = json_data['videos']
            video = videos[0]
            insights = video["insights"]
            transcriptList = insights["transcript"]
            idx = 0

            text = ""
            startTime = ""
            endTime = ""
            while (idx < len(transcriptList)):
                
                transcriptInfo = transcriptList[idx]
                text += transcriptInfo["text"] + " "
                
                instStart = transcriptInfo["instances"][0]["start"]
                instEnd = transcriptInfo["instances"][0]["end"]

                if (startTime == ""):
                    startTime = instStart
                
                if (endTime == ""):
                    endTime = instEnd
                else:
                    startTimeObj = datetime.strptime(startTime, "%H:%M:%S.%f") if ("." in startTime) else datetime.strptime(startTime, "%H:%M:%S")
                    endTimeObj = datetime.strptime(instEnd, "%H:%M:%S.%f") if ("." in instEnd) else datetime.strptime(instEnd, "%H:%M:%S")
                    
                    difference = endTimeObj - startTimeObj
                    if (idx == len(transcriptList) - 1 or difference.seconds >= TranscriptSectionDurationSeconds):
                        transcriptObj = {}
                        transcriptObj["start"] = startTime
                        transcriptObj["end"] = instEnd
                        transcriptObj["text"] = text
                        transcript.append(transcriptObj)
                        startTime = ""
                        endTime = ""
                        text = ""
                
                idx+=1

        if (isJsonL == False):
            # Write JSON format
            with open(transcriptFilename, 'w') as json_file:
                json_file.write(json.dumps(transcript))

            transcript_blob_url = self.upload_client.upload_blob(transcriptFilename)

            self.firebase.save_transcript(videoFirebaseId, transcriptFilename, transcript_blob_url)


