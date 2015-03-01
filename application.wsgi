#!/usr/bin/env python

activate_this = './venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)

from app import app as application
