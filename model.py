# -*- coding: UTF-8 -*-
import web
from configparser import ConfigParser
import sys

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it 
this.db = None

def init(filename):
    if this.db is None:
        try:
            parser = ConfigParser()
            parser.read(filename)

            # get section, default to postgresql
            db = {}
            if parser.has_section('postgresql'):
                params = parser.items('postgresql')
                for param in params:
                    db[param[0]] = param[1]

            this.db = web.database(
                dbn='postgres',
                host=db['host'],
                port=db['port'],
                user=db['user'],
                pw=db['pw'],
                db=db['db'],
            )
        except:
            this.db = None


# maths table
create_maths_table = '''CREATE TABLE maths
(id SERIAL PRIMARY KEY,
range  CHAR(32) NOT NULL,
question TEXT,
answer TEXT NOT NULL); '''

def get_answers():
    return this.db.select('maths', limit=10, order="id DESC") if this.db else None


def put_anwsers(text):
    return this.db.insert("todo", title=text) if this.db else None

