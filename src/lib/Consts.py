from dotenv import dotenv_values
from dataclasses import dataclass


@dataclass
class Consts:
    api_version: str
    api_endpoint: str
    azure_resource_manager: str
    account_name: str
    resource_group: str

    def __post_init__(self):
        if self.account_name is None or self.account_name == '' \
            or self.resource_group is None or self.resource_group == '':
            raise ValueError('Please Fill In Account Name and Resource Group on the Constant Class!')