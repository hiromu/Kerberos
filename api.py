#!/usr/bin/env python

import commands
import json
import os
import sqlite3
import uuid

import tornado.web

class ApiHandler(tornado.web.RequestHandler):
    def get(self, team_id = None):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        if team_id == None:
            cursor.execute('SELECT camps.id AS id, camps.name AS name, places.image AS image FROM camps LEFT JOIN places ON camps.place_id = places.id')
        else:
            cursor.execute('SELECT id, name FROM teams WHERE camp_id = ?', (team_id, ))

        results = [dict(zip(row.keys(), row)) for row in cursor]
        for result in results:
            if 'image' in result:
                result['image'] = self.static_url(result['image'])
        self.write(json.dumps(results))

class UploadHandler(tornado.web.RequestHandler):
    def get(self, team_id = None):
        team = None
        teams = None

        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        if team_id == None:
            cursor.execute('SELECT teams.id AS id, camps.name || \' - \' || teams.name AS name FROM teams LEFT JOIN camps ON teams.camp_id = camps.id')
            teams = [dict(zip(row.keys(), row)) for row in cursor]
        else:
            cursor.execute('SELECT teams.id AS id, camps.name || \' - \' || teams.name AS name FROM teams LEFT JOIN camps ON teams.camp_id = camps.id WHERE teams.id = ?', (team_id, ))
            row = cursor.fetchone()
            team = dict(zip(row.keys(), row))

        return self.render(os.path.join('api', 'upload.html'), team = team, teams = teams)

    def post(self, team_id = None):
        upload = self.get_argument('upload', None)

        if team_id == None:
            team = self.get_argument('team', None)
        else:
            team = team_id

        movie = self.request.files.get('file', [None])[0]
        if team == None or movie == None:
            return self.send_error(403)

        staticpath = os.path.join('uploads', str(uuid.uuid4()) + os.path.splitext(movie['filename'])[1])
        filepath = os.path.join(os.path.dirname(__file__), 'static', staticpath)
            
        handler = open(filepath, 'w')
        handler.write(movie['body'])
        handler.close()

        thumbnail = os.path.join('thumbnails', str(uuid.uuid4()) + '.png')
        result = commands.getstatusoutput('ffmpeg -i %s -ss 1 -vframes 1 -f image2 %s' % (filepath, os.path.join(os.path.dirname(__file__), 'static', thumbnail)))
        if result[0] == 0:
            self.application.db.execute('INSERT INTO movies (team_id, file, thumbnail, datetime) VALUES (?, ?, ?, datetime(\'now\', \'localtime\'))', (team, staticpath, thumbnail))
            self.application.db.commit()

            if upload == None:
                return self.write('Success')
            else:
                return self.redirect(self.reverse_url('MovieIndex', team_id))

        return self.send_error(500)

class DownloadHandler(tornado.web.RequestHandler):
    def get(self, camp_id = None):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        url_base = '%s://%s' % (self.request.protocol, self.request.host)

        if camp_id == None:
            cursor.execute('SELECT id, name FROM camps')
            camps = [dict(zip(row.keys(), row)) for row in cursor]

            return self.render(os.path.join('api', 'download.html'), camps = camps, url_base = url_base)
        else:
            cursor.execute('SELECT movies.id AS id, movies.file AS file FROM movies LEFT JOIN teams ON movies.team_id = teams.id LEFT JOIN camps ON teams.camp_id = camps.id WHERE camps.id = ?', (camp_id, ))
            movies = [dict(zip(row.keys(), row)) for row in cursor]

            return self.render(os.path.join('api', 'download_list.html'), movies = movies, url_base = url_base)
