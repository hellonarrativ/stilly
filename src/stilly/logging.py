import logging
import sys

import multiprocessing_logging

logger = None


def get_logger(handlers=None):
    global logger
    if logger:
        return logger
    logger = logging.getLogger('stilly')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    st = logging.StreamHandler(sys.stdout)
    st.setLevel(logging.DEBUG)
    st.setFormatter(formatter)
    logger.addHandler(st)
    for handler in handlers if handlers else []:
        logger.addHandler(handler)

    multiprocessing_logging.install_mp_handler(logger=logger)
    return logger
