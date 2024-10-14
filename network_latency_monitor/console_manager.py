# console_manager.py

from rich.console import Console


class NullConsole:
    """
    A NullConsole that overrides all methods of Rich's Console to do nothing.
    This effectively suppresses all console outputs when used.
    """

    def __getattr__(self, name):
        # Return a no-op function for any undefined methods
        def method(*args, **kwargs):
            pass

        return method


class ConsoleProxy:
    """
    A proxy for the Rich Console that allows dynamic reassignment.
    All modules should use console_proxy.console to perform console operations.
    """

    def __init__(self):
        self.console = Console()

    def set_console(self, new_console):
        self.console = new_console


# Instantiate a global ConsoleProxy
console_proxy = ConsoleProxy()
