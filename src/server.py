#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File transfer daemon server functionality
"""

from helper import *
import logging
import shutil
import time

__author__ = "Arun <hindol96[at]gmail.com>"

def server(logger, app_config):
	try:
		## Check if directories exists
		incoming_dir = app_config['server_directory_root'] + '/incoming'
		target_dir = app_config['server_directory_root'] + '/for-processing'

		logger.info(__file__ + ': ft-daemon (server mode) started')
		last_checked_time = 0
		while True:
			if (int(time.time()) - last_checked_time < 10):
				continue

			## check if any new file(s) exist in source dir and if they haven't
			## been modified in last 1 minute, then move them to destination (in-sync) subdir.
			for filename in os.listdir(incoming_dir):
				filepath = incoming_dir + os.path.abspath(filename)
				filesize = str(int(os.path.getsize(filepath) / 1000)) + 'KB'
				mtime = os.path.getmtime(filepath)
				curr_time = int(time.time())
				if (curr_time - mtime > 30):
					shutil.move(filepath, target_dir + '/' + filename)
					logger.info('Moved %s (%s) from %s to %s' % (filename, filesize, incoming_dir, target_dir))
				continue

			last_checked_time = int(time.time())
			time.sleep(2)

	except:
		traceback.print_exc(file=sys.stdout)
		logger.exception('Got following exception in ' + __file__)
	finally:
		logger.info(__file__ + ': ft-daemon (server mode) stopped')
