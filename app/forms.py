# -*- coding: utf-8 -*-
"""
    hackathonranks.forms
    ~~~~~~~~~~~~~~~~~~~~

    Forms for validating user input.
"""


import pytz
import wtforms_json
from wtforms import Form, validators, widgets, fields, ValidationError
from wtforms.compat import text_type, string_types


wtforms_json.init()


def monkey_patch_optional_init(func):
    """
    Monkey patches Optional.__init__ to accept nullable and blank kwargs.
    """
    def init(self, strip_whitespace=True, nullable=True, blank=True, message=None):
        if strip_whitespace:
            self.string_check = lambda s: s.strip()
        else:
            self.string_check = lambda s: s
        self.nullable = nullable
        self.blank = blank
        self.message = message

    return init


def monkey_patch_optional_call(func):
    """
    Monkey patches Optional.__call__ to handle nullable and blank.
    """
    def call(self, form, field, *args, **kwargs):
        try:
            func(self, form, field, *args, **kwargs)
        except validators.StopValidation:
            if hasattr(field, 'is_missing') and field.is_missing:
                raise validators.StopValidation()

            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message

            if field.raw_data is None:
                if self.nullable:
                    raise validators.StopValidation()
                elif self.message is None:
                    message = field.gettext('This field can not be null.')

            else:
                is_blank = (
                    isinstance(field.raw_data[0], string_types) and
                    not self.string_check(field.raw_data[0])
                )
                if is_blank and self.blank:
                    raise validators.StopValidation()
                elif self.message is None:
                    message = field.gettext('This field can not be blank.')

            raise validators.StopValidation(message)

    return call


validators.Optional.__init__ = monkey_patch_optional_init(validators.Optional.__init__)
validators.Optional.__call__ = monkey_patch_optional_call(validators.Optional.__call__)


""" Utility Functions
"""

def strip(data):
    if not data:
        return data
    else:
        return data.strip()


def lower(data):
    if not data:
        return data
    else:
        return data.lower()


def http_url(data):
    if data and not data.startswith('http://') and not data.startswith('https://'):
        return u'http://' + data
    return data


def null_if_empty(data):
    if not data:
        return None
    return data


class StringField(fields.Field):
    widget = widgets.TextInput()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        else:
            self.data = None

    def _value(self):
        return text_type(self.data) if self.data is not None else None


""" Forms
"""

class HackathonForm(Form):
    name = StringField(validators=[validators.DataRequired(), validators.Length(min=2, max=100)], filters=[strip])
    coding_starts_at = StringField(validators=[validators.DataRequired(), validators.Length(min=2, max=100)], filters=[strip])
    coding_ends_at = StringField(validators=[validators.DataRequired(), validators.Length(min=2, max=100)], filters=[strip])
    timezone = fields.StringField(validators=[validators.Optional(), validators.Length(min=1, max=120)])

    def validate_timezone(form, field):
        if field.data not in pytz.common_timezones:
            raise ValidationError('Invalid olson timezone')
