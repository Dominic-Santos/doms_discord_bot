import os
import sys
import logging

from threading import Thread

MAINTENANCE_MODE_MESSAGE = "Maintenance mode is active, try again later"


def check_dir(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_logger(name: str, filename: str = "log.txt"):
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    path = "/".join(filename.split("/")[:-1])
    if path != "":
        check_dir(path)
    handler = logging.FileHandler(filename, mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


class CustomThread(Thread):
    def __init__(self, target, args=[], kwargs={}):
        super().__init__(target=target, args=args, **kwargs)
        self.daemon = True  # Set the thread as a daemon thread
        self.return_value = None
        self.error = None

    def run(self):
        self.error = None
        try:
            self.return_value = self._target(*self._args, **self._kwargs)
        except Exception as e:
            self.error = e

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.return_value, self.error
