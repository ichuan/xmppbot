#!/usr/bin/env python
# coding: utf-8
# yc@2019/04/12

import os
import logging
import logging.handlers
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent.joinpath('logs')


def make_file_logger(name):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        # already exitst
        return logger
    logger.setLevel(os.environ.get('LOG_LEVEL') or 'INFO')
    handler = logging.handlers.RotatingFileHandler(
        filename=LOG_DIR.joinpath('{}.log'.format(name)),
        # 100MB
        maxBytes=104857600,
        backupCount=5,
    )
    handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s %(process)d %(levelname)s %(message)s'
        )
    )
    logger.addHandler(handler)
    return logger
