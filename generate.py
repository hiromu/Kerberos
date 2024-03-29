#!/usr/bin/env python
# -*- coding: utf-8 -*-

import commands
import json
import math
import os
import random
import shutil
import sqlite3
import sys
import tempfile
import time
import traceback
import uuid

from PIL import Image

STATICPATH = os.path.join(os.path.dirname(__file__), 'static')
AUDIOFILE = os.path.join(os.path.dirname(__file__), 'beautiful.m4a')
OUTPUTDIR = 'generate'

FPS = 30
RESOLUTION = (1280, 720)

BPM = 145.0
START = 190.4
END = 297.98

SECTION = [64, 64, 32]
MAXLEN = 4

ZOOMOUT = 32
MID = 24
CHANGE = FPS * 3
RATIO = 9

def animate(ratio, rmin, rmax, vinit, vend):
    b = vinit
    c = (vend - vinit)
    t = ratio - rmin
    d = rmax - rmin

    return -c / 2 * (math.cos(math.pi * t / d) - 1) + b;

def generate(files, tempdir):
    checked = []

    for filename in files:
        result = commands.getstatusoutput('ffprobe -print_format json -loglevel quiet -show_streams %s' % (os.path.join(STATICPATH, filename)))
        if result[0] != 0:
            raise Exception('Error %d: 不正なファイル (%s)' % (result[0], filename.encode('utf-8')))

        metadata = json.loads(result[1])
        minimum = 1e10
        resolution = (0, 0)

        for stream in metadata['streams']:
            minimum = min(minimum, float(stream['duration']))
            if stream['codec_type'] == 'video':
                resolution = stream['coded_width'], stream['coded_height']

        if minimum > max(60 / BPM * MAXLEN, CHANGE / FPS) and resolution == RESOLUTION:
            checked.append(filename)

    files = checked
    minimum = [len(files), None]

    def dfs(n, s, p):
        if n == len(SECTION):
            if 0 <= len(files) - s < minimum[0]:
                minimum[0] = len(files) - s
                minimum[1] = p[1:]
        else:
            m = p[-1]

            if m == 0:
                dfs(n + 1, s, p + [0])
                m = MAXLEN

            while m != 0:
                dfs(n + 1, s + SECTION[n] / m, p + [m])
                m /= 2

    dfs(0, 0, [0])

    if minimum[0] == len(files):
        raise Exception('ファイルが少なすぎます')

    pattern = minimum[1]
    random.shuffle(files)

    for i in xrange(len(files)):
        os.mkdir(os.path.join(tempdir, str(i)))
        result = commands.getstatusoutput('ffmpeg -i %s %s' % (os.path.join(STATICPATH, files[i]), os.path.join(tempdir, str(i), '%05d.png')))
    
        if result[0] != 0:
            raise Exception('Errno %d: %s を展開する際にエラーが発生しました' % (result[0], files[i].encode('utf-8')))

    count = 0
    position = START
    frame = int(START * FPS)

    Image.new('RGB', RESOLUTION, (0, 0, 0)).save(os.path.join(tempdir, 'blank.png'))

    for i in xrange(frame):
        shutil.copyfile(os.path.join(tempdir, 'blank.png'), os.path.join(tempdir, '%05d.png' % i))

    for i in xrange(len(pattern)):
        if pattern[i] == 0:
            position += 60 / BPM * SECTION[i]
            for j in xrange(frame, int(position * FPS)):
                shutil.copyfile(os.path.join(tempdir, 'blank.png'), os.path.join(tempdir, '%05d.png' % j))
            frame = int(position * FPS)
        else:
            for j in xrange(SECTION[i] / pattern[i]):
                position += 60 / BPM * pattern[i]

                for k in xrange(frame, int(position * FPS)):
                    img = Image.open(os.path.join(tempdir, str(count), '%05d.png' % (k - frame + 1)))
                    img.resize(RESOLUTION).save(os.path.join(tempdir, '%05d.png' % k))

                count += 1
                frame = int(position * FPS)

    matrix = [[(-1, random.randint(0, CHANGE - 1)) for i in xrange(RATIO)] for j in xrange(RATIO)]

    for i in xrange(RATIO):
        for j in xrange(RATIO):
            while True:
                target = random.randint(0, len(files) - 1)
                for k, l in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if 0 <= i + k < RATIO and 0 <= j + l < RATIO:
                        if matrix[i + k][j + l][0] == target:
                            break
                else:
                    matrix[i][j] = (target, matrix[i][j][1])
                    break

    mid = int((position + 60 / BPM * MID) * FPS)
    position += 60 / BPM * ZOOMOUT

    for i in xrange(frame, int(position * FPS)):
        img = Image.new('RGB', (RESOLUTION[0] * RATIO, RESOLUTION[1] * RATIO), (0, 0, 0))

        for j in xrange(len(matrix)):
            for k in xrange(len(matrix[j])):
                matrix[j][k] = (matrix[j][k][0], matrix[j][k][1] + 1)

                if matrix[j][k][1] == CHANGE:
                    while True:
                        target = random.randint(0, len(files) - 1)
                        for l, m in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            if 0 <= j + l < RATIO and 0 <= k + m < RATIO:
                                if matrix[j + l][k + m][0] == target:
                                    break
                        else:
                            matrix[j][k] = target, 0
                            break

                paste = Image.open(os.path.join(tempdir, str(matrix[j][k][0]), '%05d.png' % (matrix[j][k][1] + 1)))
                img.paste(paste, (RESOLUTION[0] * j, RESOLUTION[1] * k))

        if i < mid:
            left = int(animate(i, frame, mid, RESOLUTION[0] * (RATIO / 2), 0))
            right = int(animate(i, frame, mid, RESOLUTION[0] * (RATIO / 2 + 1), RESOLUTION[0] * RATIO))
            top = int(animate(i, frame, mid, RESOLUTION[1] * (RATIO / 2), 0))
            bottom = int(animate(i, frame, mid, RESOLUTION[1] * (RATIO / 2 + 1), RESOLUTION[1] * RATIO))
        else:
            left = 0
            right = int(RESOLUTION[0] * RATIO)
            top = 0
            bottom = int(RESOLUTION[1] * RATIO)

        img.crop((left, top, right, bottom)).resize(RESOLUTION).save(os.path.join(tempdir, '%05d.png' % i))

    frame = int(position * FPS)
    for i in xrange(frame, int(END * FPS)):
        shutil.copyfile(os.path.join(tempdir, 'blank.png'), os.path.join(tempdir, '%05d.png' % i))

    os.remove(os.path.join(tempdir, 'blank.png'))

    outputpath = os.path.join(OUTPUTDIR, str(uuid.uuid4()) + '.mp4')
    result = commands.getstatusoutput('ffmpeg -framerate %d -i %s -i %s -shortest -pix_fmt yuv420p %s' % (FPS, os.path.join(tempdir, '%05d.png'), AUDIOFILE, os.path.join(STATICPATH, outputpath)))
    if result[0] != 0:
        raise Exception('Errno %d: 出力動画のレンダリング中にエラーが発生しました' % result[0])

    return outputpath

def generate_wrapper():
    connection = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'database.db'))

    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row

    camp_id = None

    while True:
        cursor.execute('SELECT id, camp_id FROM tasks WHERE status <= 1 ORDER BY datetime ASC LIMIT 1')
        row = cursor.fetchone()

        if row != None:
            task_id = int(row['id'])
            camp_id = int(row['camp_id'])

            cursor.execute('UPDATE tasks SET status = 1 WHERE id = ?', (task_id, ))
            connection.commit()
        
            cursor.execute('SELECT movies.file AS file FROM movies LEFT JOIN teams ON movies.team_id = teams.id WHERE teams.camp_id = ?', (camp_id, ))
            files = [row['file'] for row in cursor]
        
            tempdir = tempfile.mkdtemp()
        
            try:
                res = generate(files, tempdir)
            except Exception:
                status = 3
                res = traceback.format_exc()
            else:
                status = 2
        
            shutil.rmtree(tempdir)
        
            cursor.execute('UPDATE tasks SET status = ?, message = ? WHERE id = ?', (status, res.decode('utf-8'), task_id))
            connection.commit()

            continue

        time.sleep(1)


if __name__ == '__main__':
    generate_wrapper()
