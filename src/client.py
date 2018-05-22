#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File transfer daemon client functionality
"""

from helper import *
import shutil
import time

__author__ = "Arun <hindol96[at]gmail.com>"


def client(logger, app_config):

	## Relevant directories
	source_dir = app_config['client_directory_root'] + '/new'
	insync_dir = app_config['client_directory_root'] + '/in-sync'
	archive_dir = app_config['client_directory_root'] + '/archived'

	## Get full path for file transfer tool
	ft_app_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/tools/pscp.exe'

	## Get allowed filename extensions
	filename_exts = [x.strip() for x in app_config['filename_ext'].split(',')]

	while True:
		## check if any new file(s) exist in source dir and if they haven't
		## been modified in last 1 minute, then move them to destination (in-sync) subdir.
		for filename in os.listdir(source_dir):
			extension = os.path.splitext(filename)[1]
			if extension in filename_exts:
				mtime = os.path.getmtime(os.path.abspath(filename))
				curr_time = int(time.time())
				if (curr_time - mtime > 60):
					shutil.move(os.path.abspath(filename), insync_dir + '/' + filename)
				continue
			else:
				continue

		## Check if ft app exists
		if os.path.isfile(ft_app_path):
			logger.critical(
				'File transfer tool (for client) cannot be found! Has it been removed from \'tools\' sub-directory?')
			sys.exit(3)

		server_dir = app_config['server_directory_root'] + '/incoming'

		## Send files in 'in-sync' subdir to server's appropriate dir.
		for filename in os.listdir(insync_dir):
			if sys.platform == 'win32':
				file_abspath = os.path.abspath(filename)
				cmd = "echo y | %s -l %s -pw %s %s:%s" % (
				ft_app_path, app_config['server_username'], app_config['server_passwd'], file_abspath,
				server_dir)
				output = os.system(cmd)
				if (int(output) != 0):
					logger.error('Failed to send %s to server! Error code = %d' % (file_abspath, int(output)))
				else:
					logger.info('%s successfully sent to server at %s' % (file_abspath, server_dir))
					shutil.move(file_abspath, archive_dir + '/' + filename)
					logger.info('%s moved to %s' % (file_abspath, archive_dir + '/'))

		time.sleep(10)
