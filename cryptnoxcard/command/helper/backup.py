"""
Module for handling backup of seed into the cloud
"""

import base64
from typing import Dict, List

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError
)
from cryptography.fernet import Fernet

_NUMBER_OF_BYTES = 4

# These regions give back an issue while others work. For now remove them from the options
# An error occurred (UnrecognizedClientException) when calling the ListAliases operation:
# The security token included in the request is invalid.
# TODO: Remove this when the issue has been resolved
_REGIONS_WITH_ISSUES = [
    "af-south-1",
    "ap-east-1",
    "eu-south-1",
    "me-south-1"
]


class BackupException(Exception):
    """Base exception for all seed backup exceptions"""


class ConnectionException(BackupException):
    """Issue connecting to the service"""


class ExistsException(BackupException):
    """The backup with given name already exist when creating a new one"""


class NotFoundException(BackupException):
    """When retrieving a backup it doesn't exist"""


class AWS:
    """
    Class for handling backup to AWS cloud using KMS and Secrets manager services

    :param str access_key_id: Access key id for AWS service
    :param str secret_access_key: Secret access key for AWS service

    :raises ConnectionException: There is an issue with credentials

    """

    def __init__(self, access_key_id, secret_access_key):
        self._session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        self._regions: Dict[str, str] = {
            "kms": "",
            "secretsmanager": ""
        }

        self._check_credentials()

    def backup(self, name: str, data: bytes) -> None:
        """
        Backup data under name

        :param str name: Name of the backup
        :param bytes data: Data to be backed up
        """
        data_key_encrypted, data_key_plaintext = self._create_data_key(str(name))

        cypher = Fernet(data_key_plaintext)
        encrypted_data_b64_decoded = base64.urlsafe_b64decode(
            cypher.encrypt(base64.urlsafe_b64encode(data)))

        length = len(data_key_encrypted).to_bytes(
            _NUMBER_OF_BYTES, byteorder="big")

        secret_to_store = (length + data_key_encrypted + encrypted_data_b64_decoded)

        self._create_secret(secret_to_store, name)

    def retrieve(self, name: str) -> bytes:
        """
        Retrieve a backup from AWS services

        :param str name: Name of the backup to retrieve

        :return: The retrieved backup
        :rtype: bytes
        """
        retrieved_encrypted_secret = self._get_secret(name)

        length = (int.from_bytes(retrieved_encrypted_secret[:_NUMBER_OF_BYTES], byteorder="big") +
                  _NUMBER_OF_BYTES)

        encrypted = retrieved_encrypted_secret[_NUMBER_OF_BYTES:length]

        r_data_key_plaintext = base64.b64encode(self._decrypt_data_key(encrypted))

        data_to_decrypt = base64.urlsafe_b64encode(retrieved_encrypted_secret[length:])

        cypher = Fernet(r_data_key_plaintext)

        return base64.urlsafe_b64decode(cypher.decrypt(data_to_decrypt))

    @property
    def regions(self) -> Dict[str, List[str]]:
        """
        :return: Return a list of services with regions they are available in
        :rtype: Dict[str, List[str]]
        """
        results = {}
        for service in self._regions.keys():
            regions = self._session.get_available_regions(service)
            results[service] = [x for x in regions if x not in _REGIONS_WITH_ISSUES]

        return results

    @property
    def region(self):
        return self._regions

    @region.setter
    def region(self, value: Dict[str, str]) -> None:
        """
        :param Dict[str, str] value: Service connected to a region

        :raises ValueError: The input is not valid
        """
        if set(self._regions.keys()) != set(value.keys()):
            raise ValueError

        for service, region in self.regions.items():
            if value[service] not in region:
                raise ValueError

        self._regions = value

    def _check_credentials(self):
        client = self._session.client("secretsmanager", self.regions["kms"][-1])

        try:
            client.list_secrets()
        except ClientError as error:
            if error.response["Error"]["Code"] in ["SignatureDoesNotMatch", "InvalidClientTokenId"]:
                raise ConnectionException(error.response["Error"]["Message"]) from error
            raise BackupException(error.response["Error"]["Message"])
        except EndpointConnectionError as error:
            raise BackupException(error.response["Error"]["Message"])

    def _create_data_key(self, name, key_spec="AES_256"):
        client = self._session.client("kms", self._regions["kms"])

        try:
            response = client.generate_data_key(KeyId=f"alias/{name}", KeySpec=key_spec)
        except ClientError as error:
            if error.response["Error"]["Code"] == "NotFoundException":
                try:
                    create_key_response = client.create_key(MultiRegion=False)
                    client.create_alias(AliasName=f"alias/{name}",
                                        TargetKeyId=create_key_response["KeyMetadata"]["Arn"])
                    response = client.generate_data_key(KeyId=f"alias/{name}", KeySpec=key_spec)
                except ClientError as error:
                    raise BackupException(error.response["Error"]["Message"]) from error
            else:
                raise BackupException(error.response["Error"]["Message"]) from error

        return response["CiphertextBlob"], base64.b64encode(response["Plaintext"])

    def _decrypt_data_key(self, data_key_encrypted):
        client = self._session.client("kms", self._regions["kms"])
        response = client.decrypt(CiphertextBlob=data_key_encrypted)

        return response["Plaintext"]

    def _create_secret(self, secret_value, name):
        client = self._session.client("secretsmanager", self._regions["secretsmanager"])

        try:
            response = client.create_secret(Name=name, SecretBinary=secret_value)
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceExistsException":
                raise ExistsException(error.response["Error"]["Message"]) from error
            raise BackupException(error.response["Error"]["Message"]) from error

        return response

    def _get_secret(self, name):
        client = self._session.client("secretsmanager", self._regions["secretsmanager"])

        try:
            response = client.get_secret_value(SecretId=name)
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                raise NotFoundException(error.response["Error"]["Message"]) from error
            raise BackupException(error.response["Error"]["Message"]) from error

        return response["SecretBinary"]
