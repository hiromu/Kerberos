#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3

import tornado.web

class IndexHandler(tornado.web.RequestHandler):
    def get(self, team_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT teams.id AS id, camps.id AS camp_id, camps.name AS camp_name, teams.name AS name FROM teams LEFT JOIN camps ON teams.camp_id = camps.id WHERE teams.id = ?', (team_id, ))
        row = cursor.fetchone()
        team = dict(zip(row.keys(), row))

        cursor.execute('SELECT id, datetime FROM movies WHERE team_id = ?', (team_id, ))
        movies = [dict(zip(row.keys(), row)) for row in cursor]

        return self.render(os.path.join('movie', 'index.html'), team = team, movies = movies)

class PreviewHandler(tornado.web.RequestHandler):
    def get(self, movie_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT movies.id AS id, movies.file AS file, teams.id AS team_id, camps.name AS camp_name, teams.name AS team_name FROM movies LEFT JOIN teams ON movies.team_id = teams.id LEFT JOIN camps ON teams.camp_id = camps.id WHERE movies.id = ?', (movie_id, ))
        row = cursor.fetchone()
        movie = dict(zip(row.keys(), row))

        return self.render(os.path.join('movie', 'preview.html'), movie = movie)

class DeleteHandler(tornado.web.RequestHandler):
    def get(self, movie_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT movies.id AS id, teams.id AS team_id, camps.name AS camp_name, teams.name AS team_name FROM movies LEFT JOIN teams ON movies.team_id = teams.id LEFT JOIN camps ON teams.camp_id = camps.id WHERE movies.id = ?', (movie_id, ))
        row = cursor.fetchone()
        movie = dict(zip(row.keys(), row))

        return self.render(os.path.join('movie', 'delete.html'), movie = movie)

    def post(self, movie_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT movies.team_id FROM movies WHERE id = ?', (movie_id, ))
        row = cursor.fetchone()

        cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id, ))
        self.application.db.commit()

        return self.redirect(self.reverse_url('MovieIndex', row['team_id']))
