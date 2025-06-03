import requests
from azure.identity import ClientSecretCredential, DefaultAzureCredential

from .Consts import Consts
from .Config import Config

def get_arm_access_token(config:Config) -> str:
    '''
    Get an access token for the Azure Resource Manager
    Make sure you're logged in with `az` first

    :param consts: Consts object
    :return: Access token for the Azure Resource Manager
    '''

    credential = ClientSecretCredential(
        tenant_id=config.video_indexer_app_tenant_id,
        client_id=config.video_indexer_app_client_id,
        client_secret=config.video_indexer_app_client_secret
    )

    scope = f"{config.consts.azure_resource_manager}/.default" 
    token = credential.get_token(scope)
    return token.token


def get_account_access_token_async(config:Config, arm_access_token, permission_type='Contributor', scope='Account',
                                   video_id=None):
    '''
    Get an access token for the Video Indexer account
    
    :param consts: Consts object
    :param arm_access_token: Access token for the Azure Resource Manager
    :param permission_type: Permission type for the access token
    :param scope: Scope for the access token
    :param video_id: Video ID for the access token, if scope is Video. Otherwise, not required
    :return: Access token for the Video Indexer account
    '''

    headers = {
        'Authorization': 'Bearer ' + arm_access_token,
        'Content-Type': 'application/json'
    }

    url = f'{config.consts.azure_resource_manager}/subscriptions/{config.subscription_id}/resourceGroups/{config.consts.resource_group}' + \
          f'/providers/Microsoft.VideoIndexer/accounts/{config.consts.account_name}/generateAccessToken?api-version={config.consts.api_version}'

    params = {
        'permissionType': permission_type,
        'scope': scope
    }
    
    if video_id is not None:
        params['videoId'] = video_id

    response = requests.post(url, json=params, headers=headers)
    
    # check if the response is valid
    response.raise_for_status()
    
    access_token = response.json().get('accessToken')

    return access_token