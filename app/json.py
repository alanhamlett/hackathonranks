# -*- coding: utf-8 -*-
"""
    hackathonranks.json
    ~~~~~~~~~~~~~~~~~~~

    Custom JSON Encoder and Decoder to support extra objects, including:
    datetime.time, datetime.date
"""

import datetime
import pytz
import uuid
from sqlalchemy.dialects.postgresql import UUID

from flask.json import JSONEncoder, JSONDecoder


class CustomJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.datetime):
            if o.tzinfo is not None:
                o = o.astimezone(pytz.utc)
            return o.strftime('%Y-%m-%dT%H:%M:%SZ')
        if isinstance(o, datetime.time):
            return o.strftime('%I:%M%p').lstrip('0').lower()
        if isinstance(o, datetime.date):
            return o.strftime('%m/%d/%Y')
        if isinstance(o, uuid.UUID) or isinstance(o, UUID):
            return unicode(o)
        return JSONEncoder.default(self, o)


class CustomJSONDecoder(JSONDecoder):
    """This one does not change the default behavior.
    """
