#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3

import tornado.web
import tornado.ioloop

import generate

class AddHandler(tornado.web.RequestHandler):
    def get(self, camp_id, error = ''):
        self.application.db.execute('INSERT INTO tasks (camp_id, status, datetime) VALUES (?, 0, datetime(\'now\', \'localtime\'))', (camp_id, ))
        self.application.db.commit()

        return self.redirect(self.reverse_url('TeamIndex', camp_id))

class DeleteHandler(tornado.web.RequestHandler):
    def get(self, task_id):
        task = self.latestTask(task_id)
        if task['status'] != 0:
            error = 'すでに実行中です'
        else:
            error = ''

        return self.render(os.path.join('task', 'delete.html'), task = task, error = error)

    def post(self, task_id):
        task = self.latestTask(task_id)

        if task['status'] != 0:
            return self.render(os.path.join('task', 'delete.html'), task = task, error = 'すでに実行中です')
        else:
            cursor = self.application.db.cursor()
            cursor.row_factory = sqlite3.Row

            cursor.execute('UPDATE tasks SET status = 3, message = ? WHERE id = ?', (u'中止されました', task_id))
            self.application.db.commit()

            return self.redirect(self.reverse_url('TeamIndex', task['camp_id']))

    def latestTask(self, task_id):
        cursor = self.application.db.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('SELECT camps.id AS camp_id, camps.name AS camp_name, tasks.id AS task_id, tasks.status AS status FROM tasks LEFT JOIN camps ON tasks.camp_id = camps.id WHERE tasks.id = ?', (task_id, ))
        row = cursor.fetchone()
        task = dict(zip(row.keys(), row))

        return task
