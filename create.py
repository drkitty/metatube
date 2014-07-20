#!/usr/bin/env python2

from __future__ import unicode_literals

import oursql
from copy import copy

import settings
from data import Base, engine


if __name__ == '__main__':
    s = copy(settings.database)
    s.pop('db')
    connection = oursql.Connection(**s)
    cursor = connection.cursor()

    try:
        cursor.execute('DROP DATABASE {}'.format(settings.database['db']))
    except oursql.ProgrammingError:  # database doesn't exist
        pass
    cursor.execute('CREATE DATABASE {} CHARACTER SET utf8mb4 '
                   'COLLATE utf8mb4_bin'.format(settings.database['db']))

    Base.metadata.create_all(engine)
