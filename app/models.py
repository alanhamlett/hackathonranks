# -*- coding: utf-8 -*-
"""
    hackathonranks.models
    ~~~~~~~~~~~~~~~~~~~~~

    Database models.
"""


from __future__ import division

import math
import uuid
from datetime import datetime
from sqlalchemy import not_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError

from flask import current_app as app
from flask import json
from flask.ext.sqlalchemy import SQLAlchemy


# Setup Database
db = SQLAlchemy(app)



""" Base Model
"""


class Model(db.Model):
    """Base SQLAlchemy Model for automatic serialization and
    deserialization of columns and nested relationships.

    Usage::

        >>> class User(Model):
        >>>     id = db.Column(db.Integer(), primary_key=True)
        >>>     email = db.Column(db.String(), index=True)
        >>>     name = db.Column(db.String())
        >>>     password = db.Column(db.String())
        >>>     posts = db.relationship('Post', backref='user', lazy='dynamic')
        >>>     ...
        >>>     default_fields = ['email', 'name']
        >>>     hidden_fields = ['password']
        >>>     readonly_fields = ['email', 'password']
        >>>
        >>> class Post(Model):
        >>>     id = db.Column(db.Integer(), primary_key=True)
        >>>     user_id = db.Column(db.String(), db.ForeignKey('user.id'), nullable=False)
        >>>     title = db.Column(db.String())
        >>>     ...
        >>>     default_fields = ['title']
        >>>     readonly_fields = ['user_id']
        >>>
        >>> model = User(email='john@localhost')
        >>> db.session.add(model)
        >>> db.session.commit()
        >>>
        >>> # update name and create a new post
        >>> validated_input = {'name': 'John', 'posts': [{'title':'My First Post'}]}
        >>> model.set_columns(**validated_input)
        >>> db.session.commit()
        >>>
        >>> print(model.to_dict(show=['password', 'posts']))
        >>> {u'email': u'john@localhost', u'posts': [{u'id': 1, u'title': u'My First Post'}], u'name': u'John', u'id': 1}
    """
    __abstract__ = True

    # Stores changes made to this model's attributes. Can be retrieved
    # with model.get_changes()
    _changes = {}

    def __init__(self, **kwargs):
        kwargs['_force'] = True
        self._set_columns(**kwargs)

    @classmethod
    def _get_or_create(cls, defaults={}, **kwargs):
        query = db.session.query(cls).filter_by(**kwargs)

        instance = query.first()
        if instance is not None:
            return instance, False

        db.session.begin_nested()
        try:
            kwargs.update(defaults)
            instance = cls(**kwargs)
            db.session.add(instance)
            db.session.commit()
            return instance, True

        except IntegrityError:
            db.session.rollback()
            instance = query.first()
            if instance is None:
                raise
            return instance, False

    @classmethod
    def get_or_create(cls, defaults={}, **kwargs):
        return cls._get_or_create(defaults=defaults, **kwargs)[0]

    def _set_columns(self, **kwargs):

        # TODO: stop traversing objects when no more data available

        force = kwargs.get('_force')

        readonly = []
        if hasattr(self, 'readonly_fields'):
            readonly = self.readonly_fields
        if hasattr(self, 'hidden_fields'):
            readonly += self.hidden_fields

        readonly += [
            'id',
            'created',
            'updated',
            'modified',
            'created_at',
            'updated_at',
            'modified_at',
        ]

        changes = {}

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()

        for key in columns:
            allowed = True if force or key not in readonly else False
            exists = True if key in kwargs else False
            if allowed and exists:
                val = getattr(self, key)
                if val != kwargs[key]:
                    changes[key] = {'old': val, 'new': kwargs[key]}
                    setattr(self, key, kwargs[key])

        for rel in relationships:
            allowed = True if force or rel not in readonly else False
            exists = True if rel in kwargs else False
            if allowed and exists:
                is_list = self.__mapper__.relationships[rel].uselist
                if is_list:
                    valid_ids = []
                    query = getattr(self, rel)
                    cls = self.__mapper__.relationships[rel].argument()
                    for item in kwargs[rel]:
                        if 'id' in item and query.filter_by(id=item['id']).limit(1).count() == 1:
                            obj = cls.query.filter_by(id=item['id']).first()
                            col_changes = obj.set_columns(**item)
                            if col_changes:
                                col_changes['id'] = str(item['id'])
                                if rel in changes:
                                    changes[rel].append(col_changes)
                                else:
                                    changes.update({rel: [col_changes]})
                            valid_ids.append(str(item['id']))
                        else:
                            col = cls()
                            col_changes = col.set_columns(**item)
                            query.append(col)
                            db.session.flush()
                            if col_changes:
                                col_changes['id'] = str(col.id)
                                if rel in changes:
                                    changes[rel].append(col_changes)
                                else:
                                    changes.update({rel: [col_changes]})
                            valid_ids.append(str(col.id))

                    # delete related rows that were not in kwargs[rel]
                    for item in query.filter(not_(cls.id.in_(valid_ids))).all():
                        col_changes = {
                            'id': str(item.id),
                            'deleted': True,
                        }
                        if rel in changes:
                            changes[rel].append(col_changes)
                        else:
                            changes.update({rel: [col_changes]})
                        db.session.delete(item)

                else:
                    # TODO: lazyily create related row if does not exist
                    # and check relationship's lazy attribute for smarter update
                    val = getattr(self, rel)
                    if self.__mapper__.relationships[rel].query_class is not None:
                        if val is not None:
                            col_changes = val.set_columns(**kwargs[rel])
                            if col_changes:
                                changes.update({rel: col_changes})
                    else:
                        if val != kwargs[rel]:
                            setattr(self, rel, kwargs[rel])
                            changes[rel] = {'old': val, 'new': kwargs[rel]}

        return changes

    def set_columns(self, **kwargs):
        self._changes = self._set_columns(**kwargs)
        if 'modified' in self.__table__.columns:
            self.modified = datetime.utcnow()
        if 'updated' in self.__table__.columns:
            self.updated = datetime.utcnow()
        if 'modified_at' in self.__table__.columns:
            self.modified_at = datetime.utcnow()
        if 'updated_at' in self.__table__.columns:
            self.updated_at = datetime.utcnow()
        return self._changes

    def get_changes(self):
        return self._changes

    def reset_changes(self):
        self._changes = {}

    def to_dict(self, show=None, hide=None, path=None, show_all=None):
        """ Return a dictionary representation of this model.
        """

        # TODO: stop traversing objects if can

        if not show:
            show = []
        if not hide:
            hide = []
        hidden = []
        if hasattr(self, 'hidden_fields'):
            hidden = self.hidden_fields
        default = []
        if hasattr(self, 'default_fields'):
            default = self.default_fields

        ret_data = {}

        if not path:
            path = self.__tablename__.lower()
            def prepend_path(item):
                item = item.lower()
                if item.split('.', 1)[0] == path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != '.':
                    item = '.%s' % item
                item = '%s%s' % (path, item)
                return item
            show[:] = [prepend_path(x) for x in show]
            hide[:] = [prepend_path(x) for x in hide]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        for key in columns:
            check = '%s.%s' % (path, key)
            if check in hide or key in hidden:
                continue
            if show_all or key is 'id' or check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            check = '%s.%s' % (path, key)
            if check in hide or key in hidden:
                continue
            if show_all or check in show or key in default:
                hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    ret_data[key] = []
                    if self.__mapper__.relationships[key].query_class is not None:
                        items = getattr(self, key).all()
                    else:
                        items = getattr(self, key)
                    for item in items:
                        ret_data[key].append(item.to_dict(
                            show=show,
                            hide=hide,
                            path=('%s.%s' % (path, key.lower())),
                            show_all=show_all,
                        ))
                else:
                    if self.__mapper__.relationships[key].query_class is not None or self.__mapper__.relationships[key].instrument_class is not None:
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=show,
                                hide=hide,
                                path=('%s.%s' % (path, key.lower())),
                                show_all=show_all,
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith('_'):
                continue
            check = '%s.%s' % (path, key)
            if check in hide or key in hidden:
                continue
            if show_all or check in show or key in default:
                val = getattr(self, key)
                try:
                    ret_data[key] = json.loads(json.dumps(val))
                except:
                    pass

        return ret_data


""" Database Models
"""

class User(Model):
    """User table.
    """

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    wakatime_id = db.Column(db.String(300), unique=True, nullable=False, index=True)
    wakatime_token = db.Column(db.String(300), nullable=False)
    full_name = db.Column(db.String(400))
    username = db.Column(db.String(400))
    profile_url = db.Column(db.String(4000))
    avatar_url = db.Column(db.String(4000))
    hackathons = db.relationship('Hackathon', lazy='dynamic')
    ranks = db.relationship('Rank', lazy='dynamic', backref='admin')
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime(), onupdate=datetime.utcnow)

    def __repr__(self):
        return u'User({id})'.format(
            id=self.id,
        )

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)


class Hackathon(Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    coding_starts_at = db.Column(db.DateTime(), nullable=False)
    coding_ends_at = db.Column(db.DateTime(), nullable=False)
    timezone = db.Column(db.String(200), nullable=False)
    ranks = db.relationship('Rank', backref='hackathon', lazy='dynamic')
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime(), onupdate=datetime.utcnow)

    def __repr__(self):
        return u'{name}'.format(
            name=self.name,
        )


class Rank(Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, index=True)
    hackathon_id = db.Column(UUID(as_uuid=True), db.ForeignKey('hackathon.id'), nullable=False, index=True)
    total_seconds = db.Column(db.Integer(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime(), onupdate=datetime.utcnow)

    def __repr__(self):
        return u'Rank for {user_id} at {hackathon_id}'.format(
            user_id=self.user_id,
            hackathon_id=self.hackathon_id,
        )

    @property
    def full_name(self):
        return self.user.full_name

    @property
    def username(self):
        return self.user.username

    @property
    def profile_url(self):
        return self.user.profile_url

    @property
    def avatar_url(self):
        return self.user.avatar_url

    @property
    def coding_time(self):
        hours = int(math.floor(self.total_seconds / 3600.0))
        minutes = int(math.floor(self.total_seconds / 60.0)) % 60
        seconds = self.total_seconds % 60
        coding_time = ''
        if hours > 0:
            plural = 's' if hours != 1 else ''
            coding_time = '{0} hour{1} '.format(hours, plural)
        if minutes > 0:
            plural = 's' if minutes != 1 else ''
            coding_time = '{0}{1} minute{2} '.format(coding_time, minutes, plural)
        plural = 's' if seconds != 1 else ''
        coding_time = '{0}{1} second{2} '.format(coding_time, seconds, plural)
