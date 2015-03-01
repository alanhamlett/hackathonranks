# -*- coding: utf-8 -*-
"""
    hackathonranks.logger
    ~~~~~~~~~~~~~~~~~~~~~

    Setup logging for this app.
"""


from app import app

from logging import StreamHandler, Formatter, INFO


if not app.debug:
    handler = StreamHandler()
    handler.setLevel(INFO)
    handler.setFormatter(Formatter(app.debug_log_format))
    app.logger.addHandler(handler)
    app.logger.setLevel(INFO)
