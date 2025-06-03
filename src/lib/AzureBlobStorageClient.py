import io
import os
import uuid
from azure.identity import DefaultAzureCredential #SharedTokenCacheCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier
from dotenv import dotenv_values

from .Config import Config

class AzureBlobStorageClient:

    def __init__(self, config:Config):
        self.AzureStorageAccountContainerSasUrl = config.azure_storage_container_sas_url
        self.container_client = ContainerClient.from_container_url(container_url=self.AzureStorageAccountContainerSasUrl)

    def upload_blob(self, filename):

        destFilename = os.path.basename(filename)

        print("uploading {srcFilename} > {destFilename}".format(srcFilename=filename, destFilename=destFilename))

        f = open(filename, 'rb')
        try:
            blob_client = self.container_client.get_blob_client(blob=destFilename)

            # Upload the blob data - default blob type is BlockBlob
            if (not blob_client.exists()):
                res = blob_client.upload_blob(f, blob_type="BlockBlob")
                print("uploaded file {blobUrl}".format(blobUrl=blob_client.url))
            else:
                print("file already exists")            

            return blob_client.url
            
        finally:
            f.close()
