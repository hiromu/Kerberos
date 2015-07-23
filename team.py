#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3

import tornado.web

class IndexHandler(tornado.web.RequestHandler):
    def get(self, camp_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT id, name FROM camps WHERE id = ?', (camp_id, ))
        row = cursor.fetchone()
        camp = dict(zip(row.keys(), row))

        cursor.execute('SELECT id, name FROM teams WHERE camp_id = ?', (camp_id, ))
        teams = [dict(zip(row.keys(), row)) for row in cursor]

        cursor.execute('SELECT id, status, message, datetime FROM tasks WHERE tasks.camp_id = ? ORDER BY datetime DESC', (camp_id, ))
        tasks = [dict(zip(row.keys(), row)) for row in cursor]

        return self.render(os.path.join('team', 'index.html'), camp = camp, teams = teams, tasks = tasks)

class AddHandler(tornado.web.RequestHandler):
    def get(self, camp_id, error = ''):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT id, name FROM camps WHERE id = ?', (camp_id, ))
        row = cursor.fetchone()
        camp = dict(zip(row.keys(), row))

        return self.render(os.path.join('team', 'add.html'), camp = camp, error = error)

    def post(self, camp_id):
        name = self.get_argument('name')

        if name == '':
            return self.get('チーム名を入力してください')
        
        self.application.db.execute('INSERT INTO teams (camp_id, name) VALUES (?, ?)', (camp_id, name))
        self.application.db.commit()

        return self.redirect(self.reverse_url('TeamIndex', camp_id))

class DeleteHandler(tornado.web.RequestHandler):
    def get(self, team_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT camps.id AS id, camps.name AS camp_name, teams.name AS name FROM teams LEFT JOIN camps ON teams.camp_id = camps.id WHERE teams.id = ?', (team_id, ))
        row = cursor.fetchone()
        team = dict(zip(row.keys(), row))

        return self.render(os.path.join('team', 'delete.html'), team = team)

    def post(self, team_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT camp_id FROM teams WHERE id = ?', (team_id, ))
        row = cursor.fetchone()

        cursor.execute('DELETE FROM teams WHERE id = ?', (team_id, ))
        self.application.db.commit()

        return self.redirect(self.reverse_url('TeamIndex', row['camp_id']))
