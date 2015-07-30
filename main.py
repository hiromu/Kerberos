#!/usr/bin/env python

# sqlite3> create table places (id integer primary key autoincrement, name text, image text);
# sqlite3> create table camps (id integer primary key autoincrement, place_id integer, name text, foreign key(place_id) references places(id));
# sqlite3> create table teams (id integer primary key autoincrement, camp_id integer, name text, foreign key(camp_id) references camps(id));
# sqlite3> create table movies (id integer primary key autoincrement, team_id integer, file text, thumbnail text, datetime text, foreign key(team_id) references teams(id));
# sqlite3> create table tasks (id integer primary key autoincrement, camp_id integer, status integer, message text, datetime text, foreign key(camp_id) references camps(id));

import os
import sqlite3

import tornado.web
import tornado.ioloop

import api
import camp
import team
import movie
import task

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            tornado.web.url(r'/', camp.IndexHandler, name = 'CampIndex'),
            tornado.web.url(r'/add', camp.AddHandler, name = 'CampAdd'),
            tornado.web.url(r'/delete/([0-9]+)', camp.DeleteHandler, name = 'CampDelete'),

            tornado.web.url(r'/teams/([0-9]+)', team.IndexHandler, name = 'TeamIndex'),
            tornado.web.url(r'/teams/add/([0-9]+)', team.AddHandler, name = 'TeamAdd'),
            tornado.web.url(r'/teams/delete/([0-9]+)', team.DeleteHandler, name = 'TeamDelete'),

            tornado.web.url(r'/movies/([0-9]+)', movie.IndexHandler, name = 'MovieIndex'),
            tornado.web.url(r'/movies/preview/([0-9]+)', movie.PreviewHandler, name = 'MoviePreview'),
            tornado.web.url(r'/movies/delete/([0-9]+)', movie.DeleteHandler, name = 'MovieDelete'),

            tornado.web.url(r'/tasks/add/([0-9]+)', task.AddHandler, name = 'TaskAdd'),
            tornado.web.url(r'/tasks/delete/([0-9]+)', task.DeleteHandler, name = 'TaskDelete'),

            tornado.web.url(r'/api/([0-9]+)?', api.ApiHandler),
            tornado.web.url(r'/api/upload/([0-9]+)?', api.UploadHandler, name = 'ApiUpload'),
            tornado.web.url(r'/api/download/([0-9]+)?', api.DownloadHandler, name = 'ApiDownload'),
        ]

        settings = {
            'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
        }

        self.db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'database.db'))
        self.db.execute('PRAGMA foreign_keys=ON')

        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    app = Application()
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
