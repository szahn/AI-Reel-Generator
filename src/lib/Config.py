"""
Configuration module for managing application settings.
"""
from dataclasses import dataclass
from typing import Optional
from dotenv import dotenv_values

from .Consts import Consts

@dataclass
class Config:
    """Configuration settings for the application."""
    azure_storage_account_name: str
    azure_storage_container_name: str
    subscription_id:str
    azure_storage_container_sas_url: str
    video_indexer_app_tenant_id: str
    video_indexer_app_client_id: str
    video_indexer_app_client_secret: str
    video_indexer_account_name: str
    video_indexer_resource_group: str
    video_indexer_region: str
    video_indexer_account_id: str
    replicate_api_key: str
    openai_apikey: str
    consts: Consts

    @classmethod
    def from_env(cls, env_file: str = ".env") -> 'Config':
        """
        Create a Config instance from environment variables.
        
        Args:
            env_file: Path to the .env file
            
        Returns:
            Config instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        config = dotenv_values(env_file)
        
        # Create Consts instance
        consts = Consts(
            api_version='2024-01-01',
            api_endpoint='https://api.videoindexer.ai',
            azure_resource_manager='https://management.azure.com',
            account_name=config.get('AzureVideoIndexerAccountName'),
            resource_group=config.get('AzureVideoIndexerResourceGroup')
        )
        
        return cls(
            azure_storage_account_name=config.get('AzureStorageAccountName'),
            azure_storage_container_name=config.get('AzureStorageContainerName'),
            subscription_id=config.get('AzureVideoIndexerSubscriptionId'),
            azure_storage_container_sas_url=config.get('AzureStorageAccountContainerSasUrl'),
            video_indexer_app_tenant_id=config.get('AzureVideoIndexerAppTenantId'),
            video_indexer_app_client_id=config.get('AzureVideoIndexerAppClientId'),
            video_indexer_app_client_secret=config.get('AzureVideoIndexerAppClientSecret'),
            video_indexer_account_name=config.get('AzureVideoIndexerAccountName'),
            video_indexer_resource_group=config.get('AzureVideoIndexerResourceGroup'),
            video_indexer_region=config.get('AzureVideoIndexerRegion'),
            video_indexer_account_id=config.get('AzureVideoIndexerAccountId'),
            replicate_api_key=config.get('ReplicateApiKey'),
            openai_apikey = config.get('OpenAIAPIKey'),
            consts=consts
        ) 