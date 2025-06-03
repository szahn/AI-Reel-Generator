import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime


class FirebaseDbHelper:
    cred = credentials.Certificate('./firebase-credentials.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    def __init__(self):
        pass

    def store_video_metadata(self, video_data):
        """Store video metadata in Firestore"""
        try:
            # Create a new document in the 'videos' collection
            doc_ref = FirebaseDbHelper.db.collection('videos').document()
            doc_ref.set({
                'internalId': video_data['internalId'],
                'name': video_data['name'],
                'title': video_data['title'],
                'description': video_data['description'],
                'author': video_data['author'],
                'publish_date': video_data['publish_date'],
                'keywords': video_data['keywords'],
                'video_source_url': video_data['video_source_url'],
                'videoFilename': video_data['videoFilename'],
                'audioFilename': video_data['audioFilename'],
                'created_at': datetime.now(),
                'video_thumbnail_filename': video_data['video_thumbnail_filename'],
                'video_thumbnail_blob_url': video_data['video_thumbnail_blob_url'],
                'state': 10,
                'status': 'downloaded'
            })
            print(f"Video metadata stored in Firestore with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error storing video metadata: {str(e)}")
            return None

    def get_document(self, videoFirebaseId):
        """Get video metadata from Firestore"""
        try:
            doc_ref = FirebaseDbHelper.db.collection('videos').document(f"{videoFirebaseId}")
            doc = doc_ref.get()
            return doc.to_dict()
        except Exception as e:
            print(f"Error getting firestoredocument: {str(e)}")
            return None

    def update_video_metadata(self, videoFirebaseId, videoDestUrl, audioDestUrl):
        """Update video metadata in Firestore"""
        try:
            # Create a new document in the 'videos' collection
            doc_ref = FirebaseDbHelper.db.collection('videos').document(videoFirebaseId)
            doc_ref.update({
                'state': 40,
                'video_dest_url': videoDestUrl,
                'audio_dest_url': audioDestUrl
            })
            print(f"Video metadata updated in Firestore with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error updating video metadata: {str(e)}")
            return None

    def save_transcript(self, videoFirebaseId, transcriptFilename, transcriptUrl):
        """Update video metadata in Firestore"""
        try:
            # Create a new document in the 'videos' collection
            doc_ref = FirebaseDbHelper.db.collection('videos').document(videoFirebaseId)
            doc_ref.update({
                'state': 60,
                'transcript_url': transcriptUrl,
                'transcript_filename': transcriptFilename
            })
            print(f"Video metadata updated in Firestore with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error updating video metadata: {str(e)}")
            return None

    def save_summary(self, videoFirebaseId, summaryFilename, summaryUrl):
        """Update video metadata in Firestore"""
        try:
            # Create a new document in the 'videos' collection
            doc_ref = FirebaseDbHelper.db.collection('videos').document(videoFirebaseId)
            doc_ref.update({
                'state': 80,
                'summary_url': summaryUrl,
                'summary_filename': summaryFilename
            })
            print(f"Video metadata updated in Firestore with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error updating video metadata: {str(e)}")
            return None

    def save_reels(self, videoFirebaseId, reels_metadata):
        """Update video metadata in Firestore"""
        try:
            # Create a new document in the 'videos' collection
            doc_ref = FirebaseDbHelper.db.collection('videos').document(videoFirebaseId)
            doc_ref.update({
                'reels': reels_metadata,
                'state': 100,
                'status': 'processed'
            })
            print(f"Video metadata updated in Firestore with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error updating video metadata: {str(e)}")
            return None
