# -*- coding: UTF-8 -*-
import web

db = web.database(
    dbn='postgres',
    host='127.0.0.1',
    port=10090,
    user='postgres',
    pw='pcommonP@55',
    db='demodb',
)

# maths table
create_maths_table = '''CREATE TABLE maths
(id SERIAL PRIMARY KEY,
range  CHAR(32) NOT NULL,
question TEXT,
answer TEXT NOT NULL); '''

def get_answers():
    return db.select('maths', limit=10, order="id DESC")


def put_anwsers(text):
    db.insert("todo", title=text)