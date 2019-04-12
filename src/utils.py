#!/usr/bin/env python
# coding: utf-8
# yc@2019/04/12

import os
import logging
import logging.handlers
import subprocess
from pathlib import Path
from tempfile import TemporaryFile


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


def shell(cmd):
    # subprocess.check_output() limits stdout to 64KB
    with TemporaryFile() as stdout:
        with TemporaryFile() as stderr:
            subprocess.call(cmd, stdout=stdout, stderr=stderr)
            stderr.seek(0)
            errs = stderr.read()
            if errs:
                raise ValueError(errs)
            stdout.seek(0)
            return stdout.read()
