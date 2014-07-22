#!/usr/bin/env python

import data


s = data.Session()
for video in s.query(data.Video):
    print u'+++ Downloading {} +++'.format(video.title)
    video.download()
del s
