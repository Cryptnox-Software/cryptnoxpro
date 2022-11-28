from pathlib import Path
from typing import Tuple

import boto3
import cryptnoxpy
from botocore.client import BaseClient as AwsClient
from botocore.exceptions import ClientError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    load_der_public_key,
    PublicFormat
)

from ..user_key_base import (
    ProcessingException,
    UserKey
)
from ...helper.ui import input_with_exit


class AwsKms(UserKey):
    name = 'aws_kms'
    description = 'AWS KMS'
    priority = 200
    slot_index = cryptnoxpy.SlotIndex.EC256R1
    custom_bit = 1

    KEY_ID = 'cryptnox_card_open'
    REGION_NAME = 'eu-north-1'

    def delete(self) -> None:
        access_key_id, secret_access_key, region_name, alias = AwsKms._config()
        client = AwsKms._client(access_key_id, secret_access_key, region_name)

        try:
            client.schedule_key_deletion(KeyId=alias, PendingWindowInDays=7)
        except ClientError as error:
            raise ProcessingException(error) from error

        print('The AWS KMS key has been scheduled for deletion and will be deleted after 7 days')

    @property
    def public_key(self) -> bytes:
        access_key_id, secret_access_key, region_name, alias = AwsKms._config()
        client = AwsKms._client(access_key_id, secret_access_key, region_name)
        try:
            public_key = self._public_key(client, alias)
        except ClientError as error:
            raise ProcessingException(error) from error

        return public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

    def sign(self, message: bytes) -> bytes:
        access_key_id, secret_access_key, region_name, alias = AwsKms._config()
        client = AwsKms._client(access_key_id, secret_access_key, region_name)
        try:
            return client.sign(KeyId=alias, Message=message, MessageType='RAW',
                               SigningAlgorithm='ECDSA_SHA_256')['Signature']
        except ClientError as error:
            raise ProcessingException(error) from error

    @staticmethod
    def _client(access_key_id: str, secret_access_key: str, region_name: str) -> AwsClient:
        try:
            session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                    region_name=region_name)
            return session.client('kms')
        except ClientError as error:
            raise ProcessingException(error) from error

    @staticmethod
    def _config() -> Tuple[str, str, str, str]:
        file = Path.home().joinpath('cryptnox.csv')
        try:
            with open(file.absolute(), 'r') as config:
                data = config.readlines()
        except FileNotFoundError as error:
            print(f'AWS configuration not found in expected location: {file}')
            while True:
                file_path = input_with_exit('Path (exit): ')
                file = Path.home().joinpath(file_path)
                try:
                    with open(file.absolute(), 'r') as config:
                        data = config.readlines()
                except FileNotFoundError as error:
                    raise ProcessingException(error) from error
                else:
                    break

        try:
            access_key_id = data[0][15:].strip()
            secret_access_key = data[1][13:].strip()
        except IndexError as error:
            raise ProcessingException('Error in reading csv configuration') from error

        try:
            region_name = data[2][7:].strip()
        except IndexError:
            region_name = AwsKms.REGION_NAME
            print(f'Region name not found in configuration. Using default: {AwsKms.REGION_NAME}')

        try:
            alias = data[3][6:].strip()
        except IndexError:
            alias = AwsKms.KEY_ID
            print(f'Alias not found in configuration. Using default: {AwsKms.KEY_ID}')
        alias = 'alias/' + alias

        return access_key_id, secret_access_key, region_name, alias

    @staticmethod
    def _create_key(client: AwsClient, alias: str) -> EllipticCurvePublicKey:
        try:
            arn = client.create_key(
                Description='Key for opening cryptnox card',
                KeyUsage='SIGN_VERIFY',
                KeySpec='ECC_NIST_P256',
                MultiRegion=False
            )["KeyMetadata"]["Arn"]

            client.create_alias(AliasName=alias, TargetKeyId=arn)

            response = client.get_public_key(KeyId=alias)

        except (ClientError, KeyError) as error:
            raise ProcessingException(error) from error

        return response['PublicKey']

    @staticmethod
    def _public_key(client: AwsClient, alias: str) -> EllipticCurvePublicKey:
        try:
            public_key = client.get_public_key(KeyId=alias)['PublicKey']
        except ClientError as error:
            if error.response["Error"]["Code"] == "NotFoundException":
                public_key = AwsKms._create_key(client, alias)
            else:
                raise ProcessingException(error) from error
        except KeyError as error:
            raise ProcessingException(error) from error

        return load_der_public_key(public_key, backend=default_backend())
