#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Various helpers functions
"""

import os
import sys
import inspect
import traceback
import errno
import subprocess
import logging
import ConfigParser

__author__ = "Arun <aghose@i2r.a-star.edu.sg>"

## App config parameters
app_config = {
	'app_mode': '',
	'server_username': '',
	'server_passwd ': '',
	'client_directory_root': '',
	'server_directory_root': '',
	'filename_ext': ''
}


def parse_config_file(filepath, logger):
	"""Reads and parses given config file to retrieve necessary program parameters"""
	global app_config

	try:
		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.read(filepath)

		app_config['app_mode'] = config.getint('General', 'app_mode')
		app_config['server_username'] = config.get('Authentication', 'server_username')
		app_config['server_passwd'] = config.get('Authentication', 'server_passwd')
		app_config['client_directory_root'] = config.get('Client', 'client_directory_root')
		app_config['server_directory_root'] = config.get('Server', 'server_directory_root')
		app_config['filename_ext'] = config.get('Log', 'filename_ext')

		if app_config['app_mode'] is None or not app_config['app_mode']:
			logger.error("'app_mode' is missing in config file.")
			sys.exit(1)
		if app_config['server_username'] is None or not app_config['server_username']:
			logger.error("'server_username' is missing in config file.")
			sys.exit(1)
		if app_config['server_passwd'] is None or not app_config['server_passwd'] \
				or ' ' in app_config['server_passwd']:
			logger.error("'server_passwd' is missing in config file or invalid 'server_passwd'.")
			sys.exit(1)

		if app_config['app_mode'] == 'client':
			if app_config['client_directory_root'] is None or not app_config['client_directory_root'] \
					or ' ' in app_config['client_directory_root']:
				logger.error("'client_directory_root' is missing in config file or invalid 'client_directory_root'.")
				sys.exit(1)
			if app_config['filename_ext'] is None:
				logger.error("'filename_ext' is missing in config file.")
				sys.exit(1)
		elif app_config['app_mode'] == 'server':
			if app_config['server_directory_root'] is None or not app_config['server_directory_root']\
					or ' ' in app_config['server_directory_root']:
				logger.error("'server_directory_root' is missing in config file or invalid 'server_directory_root'.")
				sys.exit(1)
		else:
			logger.error("'app_mode' is Invalid!")
			sys.exit(1)

	except:
		raise


def create_logger(name):
	## Create logger
	logger = logging.getLogger('ft-daemon')
	logger.setLevel(logging.DEBUG)
	logger.propagate = False
	return logger


def add_fh_to_logger(logger):
	## Add file hanlder to logger
	if sys.platform == 'win32':
		log_file_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '\logs\\ft-daemon.log'
	else:
		log_file_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/logs/ft-daemon.log'
	fh = logging.FileHandler(log_file_path, 'w')
	fh.setLevel(logging.DEBUG)
	logger.addHandler(fh)
	keep_fds = [fh.stream.fileno()]
	return keep_fds


def create_dir_root(app_mode, dir_root_path, logger):
	if app_mode == 'server' or app_mode == 'server':
		## Create directory root
		try:
			os.makedirs(dir_root_path)
		except OSError as exc:  # Python >2.5
			if exc.errno == errno.EEXIST and os.path.isdir(dir_root_path):
				pass
			else:
				raise
		## Create all subdirectories
		try:
			if app_mode == 'server':
				os.makedirs(dir_root_path + '/incoming')
				os.makedirs(dir_root_path + '/for-processing')
				os.makedirs(dir_root_path + '/processed')
			else:
				os.makedirs(dir_root_path + '/new')
				os.makedirs(dir_root_path + '/in-sync')
				os.makedirs(dir_root_path + '/archived')
		except OSError as exc:  # Python >2.5
			if exc.errno == errno.EEXIST and os.path.isdir(dir_root_path):
				pass
			else:
				raise
	else:
		raise ValueError('Invalid app_mode')


def create_user(username, passwd, dir_root_path, logger):
	"""This is for Linux or similar OS only"""
	output = subprocess.check_output('id -u ' + username + ' 2>/dev/null | wc -l', shell=True)
	if int(output) == 0:
		logger.info('User account for file transfer does not exist! This application will try to create it...')
	else:
		return 0
	uid = os.getuid()
	if int(uid) != 0:
		logger.info('Please re-run this application as root/sudo to create user for client to send files.')
		sys.exit()

	os.system("useradd -p $(makepasswd --clearfrom=- --crypt-md5 <<< " + passwd + " | awk '{print $2}' | tr -d '\n') -s /bin/bash " + username)
	os.system('chgrp -R ' + username + ' ' + dir_root_path + '/new')
	return 0


def module_exists(name):
	import imp
	try:
		imp.find_module('daemonize')
		found = True
	except ImportError:
		found = False
	return found
