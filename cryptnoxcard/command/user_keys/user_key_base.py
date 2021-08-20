"""
Module containing base class for user key
"""
import abc

import cryptnoxpy


class UserKeyException(Exception):
    """
    Base exception for all exceptions for UserKey
    """


class ExitException(UserKeyException):
    """
    The user has exited the request
    """


class NotFoundException(UserKeyException):
    """
    The user key hasn't been found
    """


class NotSupportedException(UserKeyException):
    """
    The user key is not supported
    """


class ProcessingException(UserKeyException):
    """
    There was an issue in processing the user key
    """


class UserKey(metaclass=abc.ABCMeta):
    """
    Base class on top of which other user key classes should be implemented
    """
    priority: int = 0

    def __init__(self, target: str = ""):
        self._target: str = target

    @abc.abstractmethod
    def delete(self) -> None:
        """
        Delete the key from the user key provider
        """

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """
        :return: Description of the user key service
        :rtype: str
        """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        :return: Name of the user key service
        :rtype: str
        """

    @property
    @abc.abstractmethod
    def public_key(self) -> bytes:
        """
        :return: Public key of the user key service
        :rtype: bytes
        """

    @abc.abstractmethod
    def sign(self, message: bytes) -> bytes:
        """
        Get signature of message from user key service

        :param bytes message: Message to sign

        :return: Signature of the given message
        :rtype: bytes
        """

    @property
    @abc.abstractmethod
    def slot_index(self) -> cryptnoxpy.SlotIndex:
        """
        :return: Compatible slot index on the card
        :rtype: cryptnoxpy.SlotIndex
        """

    @classmethod
    def __subclasshook__(cls, c):
        if cls is UserKey:
            attrs = set(dir(c))

            if set(cls.__abstractmethods__) <= attrs:
                return True

        return NotImplemented
