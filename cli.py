"""
Command-line interface for the reel generator application.
"""
import argparse
import logging
import sys
from typing import Optional

from .processor import VideoProcessor
from .exceptions import VideoProcessingError

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process videos and generate reels'
    )
    
    parser.add_argument(
        '--video-url',
        required=True,
        help='URL of the video to process'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args(args)

def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parsed_args = parse_args(args)
    setup_logging(parsed_args.verbose)
    
    try:
        processor = VideoProcessor()
        processor.process_video(parsed_args.video_url)
        return 0
    except VideoProcessingError as e:
        logger.error(f"Error processing video: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 