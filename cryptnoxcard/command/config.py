# -*- coding: utf-8 -*-
"""
Module containing command for handling configuration file
"""

from .command import Command
from .helper.config import (
    write_config,
    print_key_config,
    print_section_config,
    read_config
)

try:
    import enums
except ImportError:
    from .. import enums


class Config(Command):
    """
    Command for handling configuration file
    """
    _name = enums.Command.CONFIG.value

    def _execute(self, card) -> int:
        if self.data.value:
            return write_config(card.serial_number,
                                self.data.section, self.data.key,
                                self.data.value)
        if self.data.key:
            return print_key_config(card.serial_number,
                                    self.data.section, self.data.key)
        if self.data.section:
            return print_section_config(card.serial_number,
                                        self.data.section)

        read_config(card.serial_number)

        return 0
