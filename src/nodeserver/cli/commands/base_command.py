
from abc import ABC, abstractmethod
from argparse import _SubParsersAction, ArgumentParser, Namespace


class CLICommand(ABC):
    @classmethod
    def register_command(cls, subparsers: _SubParsersAction[ArgumentParser]):
        parser = cls.on_register_command(subparsers)
        parser.set_defaults(func=cls.run)

    @classmethod
    @abstractmethod
    def on_register_command(cls, subparsers: _SubParsersAction[ArgumentParser]) -> ArgumentParser:
        pass

    @classmethod
    @abstractmethod
    def run(cls, args: Namespace):
        pass
