#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File transfer daemon server functionality
"""

from helper import *
import logging
import shutil
import time

__author__ = "Arun <aghose@i2r.a-star.edu.sg>"


def server(logger, app_config):

	## Check if directories exists
	incoming_dir = app_config['server_directory_root'] + '/incoming'
	target_dir = app_config['server_directory_root'] + '/for-processing'

	while True:

		## check if any new file(s) exist in source dir and if they haven't
		## been modified in last 1 minute, then move them to destination (in-sync) subdir.
		for filename in os.listdir(incoming_dir):
			mtime = os.path.getmtime(os.path.abspath(filename))
			curr_time = int(time.time())
			if (curr_time - mtime > 60):
				shutil.move(os.path.abspath(filename), target_dir + '/' + filename)
			continue

		time.sleep(10)
