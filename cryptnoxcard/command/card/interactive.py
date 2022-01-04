from argparse import Namespace

from . import options
from ..helper.cards import Cards

try:
    from interactive_cli import InteractiveCli
except ImportError:
    from ... interactive_cli import InteractiveCli


class Interactive(InteractiveCli):
    def _command(self, data: Namespace, cards: Cards = None, card_type: int = 0):
        from . import factory
        return factory.command(data, cards, card_type)

    def _prepare_parser(self) -> None:
        super()._prepare_parser()

        options.add(self.parser, True)
