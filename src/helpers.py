import os
import sys
import logging

def check_dir(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_logger(name: str, filename: str ="log.txt"):
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