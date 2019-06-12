import sys
from typing import IO, Optional, Any


class Logger:
    _output = None

    def __init__(self, output: Optional[IO] = None):
        self._output = output

    def console(self, message: str, end: str = '\n'):
        """
        Write message with end as the last character to sys.stdout, if it is a terminal.
        :param message: The message to write
        :param end: The last character
        """
        if self._output is None and sys.stdout.isatty():
            sys.stdout.write(message + end)

    def log(self, prefix: str, message: str):
        """
        Write the given message appended to the prefix to the logfile or stdout
        :param prefix: A prefix
        :param message: The message to write
        """
        if self._output is None:
            print(prefix + ' ' + message)
            sys.stdout.flush()
        else:
            self._output.write(prefix + ' ' + message + '\n')
            self._output.flush()

    def debug(self, message: str):
        self.log('[Debug]', message)

    def info(self, message: str):
        self.log('[Info ]', message)

    def warn(self, message: str):
        self.log('[Warn ]', message)

    def error(self, message: str):
        self.log('[ERROR]', message)

    def getOutput(self) -> Optional[IO]:
        """
        :return: The output fileobject of this logger or None
        """
        return self._output


class Loggable(object):
    def __init__(self, logger: Logger, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._logger = logger

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warn(self, message: str):
        self._logger.warn(message)

    def error(self, message: str):
        self._logger.error(message)