from os import getcwd
from json.decoder import JSONDecodeError
from json import load, dump
from logging import getLogger

NAME = 'config_manager'
PATH = '//config.json'

logger = getLogger(NAME)

def dump_to_config(dict):
    logger.debug("%s.dump_to_config()", NAME)
    my_dict = load_from_config()

    dir = f"{getcwd()}{PATH}"
    for k in dict.keys():
        my_dict[k] = dict[k]

    with open(dir, 'w') as f:
        dump(my_dict, f, indent=4)

def load_from_config(key=None):
    dir = f"{getcwd()}{PATH}"
    try:
        with open(dir, 'r') as f:
            try:
                my_dict = load(f)
            except JSONDecodeError:
                logger.error('%s Empty config file.', NAME)
                return {}
    except FileNotFoundError:
        logger.error('%s No config file.', NAME)
        return {}

    if key is None:
        return my_dict
    else:
        return my_dict[key]
