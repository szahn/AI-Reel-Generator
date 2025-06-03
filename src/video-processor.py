import argparse
import pprint
from lib.VideoProcessor import VideoProcessor
from lib.Config import Config

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Video Processor')
    parser.add_argument('--videoUrl')
    args = parser.parse_args()

    videoProcessor = VideoProcessor(Config.from_env())
    processResults = videoProcessor.process_video(args.videoUrl)
    pprint(processResults)