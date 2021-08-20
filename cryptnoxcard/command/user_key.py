# -*- coding: utf-8 -*-
"""
Module containing command for working with user keys like:
YubiKey or Windows Hello
"""
import shutil
from typing import Callable

import cryptnoxpy
from tabulate import tabulate

from . import user_keys
from .command import Command
from .helper import security

try:
    import enums
except ImportError:
    from .. import enums


class UserKey(Command):
    """
    Command to work with user keys.
    """
    _name = enums.Command.USER_KEY.value

    def _execute(self, card: cryptnoxpy.Card) -> int:
        if self.data.subaction == "list":
            return self._list(card)
        if self.data.subaction == "add":
            return UserKey._add(card, self.data.type, " ".join(self.data.description))
        if self.data.subaction == "delete":
            return UserKey._delete(card, self.data.type)

        return -1

    @staticmethod
    def _add(card: cryptnoxpy.Card, auth_type: str, description: str = "") -> int:
        result = -1
        if card.user_key_enabled(user_keys.get()[auth_type]):
            print("Card has already key of this type.")
            return -1

        if security.process_command_with_puk(card, user_keys.add, auth_type, card, description):
            print("User key added")
            result = 0

        return result

    @staticmethod
    def _delete(card: cryptnoxpy.Card, auth_type: str) -> int:
        result = -1
        if not card.user_key_enabled(user_keys.get()[auth_type]):
            print("Key not found exist.")
            return -1

        if security.process_command_with_puk(card, user_keys.delete, auth_type, card):
            print("User key deleted.")
            result = 0

        return result

    def _list(self, card: cryptnoxpy.Card) -> int:
        slots = user_keys.get()
        data = [[name] for name, slot in slots.items() if card.user_key_enabled(slot)]

        if not data:
            print("No user keys registered in card")
            return 0

        self._check(card)

        large_screen = shutil.get_terminal_size((80, 20)).columns > 200
        key_length = 128 if large_screen else 32
        headers = ["Type", "Description", "Public Key"]

        for row in data:
            slot = slots[row[0]]
            if card.user_key_enabled(slot):
                description, public_key = card.user_key_info(slot)
                row.append(description)
                row.append("\n".join([public_key[i:i + key_length]
                                      for i in range(0, len(public_key), key_length)]))

        print(tabulate(data, headers=headers))

        return 0

