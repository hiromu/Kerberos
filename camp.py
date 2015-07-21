#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import uuid

import tornado.web

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT id, name FROM camps')
        camps = [dict(zip(row.keys(), row)) for row in cursor]

        cursor.execute('''SELECT * FROM (
                SELECT tasks.id AS id, camps.name AS name, tasks.status AS status, tasks.message AS message, tasks.datetime AS datetime FROM tasks LEFT JOIN camps ON tasks.camp_id = camps.id WHERE tasks.status <= 1
            ) UNION SELECT * FROM (
                SELECT tasks.id AS id, camps.name AS name, tasks.status AS status, tasks.message AS message, tasks.datetime AS datetime FROM tasks LEFT JOIN camps ON tasks.camp_id = camps.id WHERE tasks.status >= 2 ORDER BY datetime DESC LIMIT 10
            ) ORDER BY datetime DESC''')
        tasks = [dict(zip(row.keys(), row)) for row in cursor]

        return self.render(os.path.join('camp', 'index.html'), camps = camps, tasks = tasks)

class AddHandler(tornado.web.RequestHandler):
    def get(self, error = ''):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT id, name FROM places')
        places = [dict(zip(row.keys(), row)) for row in cursor]

        return self.render(os.path.join('camp', 'add.html'), places = places, error = error)

    def post(self):
        place = self.get_argument('place')
        name = self.get_argument('name')

        if name == '':
            return self.get('キャンプ名を入力してください')
        
        if place == '-1':
            placename = self.get_argument('placename')
            if placename == '':
                return self.get('会場名を入力してください')

            background = self.request.files.get('background', [None])[0]
            if background == None:
                return self.get('背景画像を設定してください')

            staticpath = os.path.join('images', str(uuid.uuid4()) + os.path.splitext(background['filename'])[1])
            filepath = os.path.join(os.path.dirname(__name__), 'static', staticpath)

            with open(filepath, 'w') as handler:
                handler.write(background['body'])

                cursor = self.application.db.cursor()
                cursor.execute('INSERT INTO places (name, image) VALUES (?, ?)', (placename, staticpath))
                place = cursor.lastrowid
                self.application.db.commit()

        self.application.db.execute('INSERT INTO camps (place_id, name) VALUES (?, ?)', (place, name))
        self.application.db.commit()

        return self.redirect(self.reverse_url('CampIndex'))

class DeleteHandler(tornado.web.RequestHandler):
    def get(self, camp_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT name FROM camps WHERE id = ?', (camp_id, ))
        row = cursor.fetchone()

        return self.render(os.path.join('camp', 'delete.html'), camp = dict(zip(row.keys(), row)))

    def post(self, camp_id):
        self.application.db.execute('DELETE FROM camps WHERE id = ?', (camp_id, ))
        self.application.db.commit()

        return self.redirect(self.reverse_url('CampIndex'))
