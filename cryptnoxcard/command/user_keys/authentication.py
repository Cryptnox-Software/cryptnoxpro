"""
Module for handling user authentication using third party solutions signature.
"""
import importlib
from pathlib import Path
from typing import Dict

import cryptnoxpy

from . import user_key_base

for path in Path(__file__).parent.iterdir():
    if path.is_dir():
        importlib.import_module("." + path.name, package=__package__)


def add(name: str, card: cryptnoxpy.Card, description: str, puk: str) -> bool:
    """
    Add user key defined by name to the card

    :param str name: Name of user key to add to the card
    :param cryptnox.Card card: Card to which to add the user key
    :param str description: Description of the user key
    :param str puk: PUK code of the card

    :return: Whether the key was added
    :rtype: bool
    """
    for user_key_cls in user_key_base.UserKey.__subclasses__():
        if user_key_cls.name != name:
            continue

        try:
            user_key = user_key_cls("cryptnox_card" + str(card.serial_number))
        except user_key_base.NotSupportedException as error:
            print(error)
            return False

        if card.user_key_enabled(user_key.slot_index):
            print("Key already exist. First delete the existing one.")
            return False
        description = description or user_key.description
        try:
            public_key = user_key.public_key
        except user_key_base.UserKeyException:
            return False

        card.user_key_add(user_key.slot_index, description, public_key, puk)

        return True

    return False


def authenticate(card: cryptnoxpy.Card, message: bytes = b"") -> bool:
    """
    Authenticate the card by using a signature from third party

    :param cryptnoxpy.Card card: Card to use to authenticate
    :param bytes message: Message to sign to open the card, if left empty, challenge-response
                          authentication will be used

    :return: Authorization was successful
    :rtype: bool
    """
    result = False

    user_key_classes = user_key_base.UserKey.__subclasses__()
    user_key_classes.sort(key=lambda x: x.priority, reverse=True)

    digest = message if message else card.user_key_challenge_response_nonce()

    for user_key_cls in user_key_classes:
        try:
            user_key = user_key_cls("cryptnox_card" + str(card.serial_number))
        except user_key_base.NotSupportedException:
            continue

        if not card.user_key_enabled(user_key.slot_index):
            continue

        try:
            signature = user_key.sign(digest)
        except user_key_base.NotFoundException:
            continue
        except user_key_base.UserKeyException as error:
            print(f"{user_key.name}: {error}")
        else:
            if message:
                result = card.user_key_signature_open(user_key.slot_index, message, signature)
            else:
                result = card.user_key_challenge_response_open(user_key.slot_index, signature)

            if result:
                break

    return result


def delete(name: str, card: cryptnoxpy.Card, puk: str) -> bool:
    """
    Delete the key from the card

    :param str name: Name of the service which to delete
    :param cryptnoxpy.Card card: Card to use
    :param str puk: PUK code of card
    """
    for user_key_cls in user_key_base.UserKey.__subclasses__():
        if user_key_cls.name != name:
            continue

        try:
            user_key = user_key_cls("cryptnox_card" + str(card.serial_number))
        except user_key_base.NotSupportedException as error:
            print(error)
            return False

        if not card.user_key_enabled(user_key.slot_index):
            print("Key not found exist.")
            break

        try:
            user_key.delete()
        except user_key_base.UserKeyException:
            pass

        card.user_key_delete(user_key.slot_index, puk)
        return True

    return False


def get() -> Dict[str, cryptnoxpy.SlotIndex]:
    """
    Get all user key module names and the slot index they are connected to on the card

    :return: A dictionary containing names of services with the slot they take on card
    :rtype: Dict[str, cryptnoxpy.SlotIndex]
    """
    user_keys = {}

    user_key_classes = user_key_base.UserKey.__subclasses__()
    user_key_classes.sort(key=lambda x: x.priority, reverse=True)

    for user_key_cls in user_key_classes:
        try:
            user_key = user_key_cls()
        except user_key_base.NotSupportedException as error:
            print(error)
            continue

        user_keys[user_key.name] = user_key.slot_index

    return user_keys
