from typing import List

from stdiomask import getpass
from tabulate import tabulate


class ExitException(Exception):
    """Raised when user has indicated he want's to exit the command"""


def input_with_exit(text, required=True, input_method=None):
    input_method = input_method or input
    while True:
        value = input_method(text).strip()
        if value.lower() == "exit":
            raise ExitException
        if required and not value:
            print("This entry is required")
        else:
            break

    return value


def option_input(options: List[str], name: str = ""):
    name = name or "option"
    print(tabulate(enumerate(options, 1)))
    length = len(options)

    while True:
        choice = input_with_exit(f"\nChoose {name} (1 - {length}): ")

        try:
            return options[int(choice) - 1]
        except (IndexError, ValueError):
            print(f"Please, enter a number between 1 and {length}")


def print_warning(text):
    print()
    print(tabulate([[str(text).upper()]], tablefmt="rst"))
    print()


def secret_with_exit(text, required=True):
    return input_with_exit(text, required, getpass)
