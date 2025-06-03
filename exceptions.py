"""
Custom exceptions for the reel generator application.
"""

class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    pass

class VideoDownloadError(VideoProcessingError):
    """Exception raised when video download fails."""
    pass

class VideoUploadError(VideoProcessingError):
    """Exception raised when video upload fails."""
    pass

class VideoIndexingError(VideoProcessingError):
    """Exception raised when video indexing fails."""
    pass

class TranscriptProcessingError(VideoProcessingError):
    """Exception raised when transcript processing fails."""
    pass

class ReelGenerationError(VideoProcessingError):
    """Exception raised when reel generation fails."""
    pass 