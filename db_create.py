#!/usr/bin/env python

import os
import sys

from app.models import db
from app.config import BASE_DIR, ALEMBIC_CONFIG, DB_HOST, DB_NAME

from alembic import command
from alembic.config import Config


def main():

    if not os.path.exists(os.path.join(BASE_DIR, 'alembic/versions')):
        os.mkdir(os.path.join(BASE_DIR, 'alembic/versions'))

    force = True if len(sys.argv) > 1 and sys.argv[1] == '--force' else False
    if force or raw_input('Really drop and recreate all tables on %s:%s? (Y/N)' % (DB_HOST, DB_NAME)) == 'Y':
        db.drop_all()
        db.session.execute('DROP TABLE IF EXISTS alembic_version')
        db.session.commit()
        db.create_all()
        print 'Created all tables on %s:%s.' % (DB_HOST, DB_NAME)
        alembic_cfg = Config(ALEMBIC_CONFIG)
        command.stamp(alembic_cfg, 'head')
        print 'Setup Alembic for database migrations.'
    else:
        print 'Exiting.'
    return 0


if __name__ == '__main__':
    sys.exit(main())
