#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Various helpers functions
"""

import os
import sys
import traceback
import errno
import subprocess
import logging
import logging.handlers
import ConfigParser

__author__ = "Arun <hindol96[at]gmail.com>"

## App config parameters
app_config = {
	'app_mode': '',
	'server_username': '',
	'server_passwd ': '',
	'client_directory_root': '',
	'server_directory_root': '',
	'server_hostname': '',
}


def parse_config_file(logger):
	"""Reads and parses given config file to retrieve necessary program parameters"""
	global app_config

	try:
		if sys.platform == 'win32':
			filepath = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '\config\\ft-daemon.conf'
		else:
			filepath = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/config/ft-daemon.conf'

		if not os.path.exists(filepath):
			logger.error("Config file is missing!")
			os._exit(1)

		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.read(filepath)

		app_config['app_mode'] = config.get('General', 'app_mode')

		app_config['server_username'] = config.get('Authentication', 'server_username')
		app_config['server_passwd'] = config.get('Authentication', 'server_passwd')
		app_config['client_directory_root'] = config.get('Client', 'client_directory_root')
		app_config['server_directory_root'] = config.get('Server', 'server_directory_root')
		app_config['server_hostname'] = config.get('Client', 'server_hostname')
		app_config['filename_ext'] = config.get('Client', 'filename_ext')

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
		if app_config['server_directory_root'] is None or not app_config['server_directory_root'] \
				or ' ' in app_config['server_directory_root']:
			logger.error("'server_directory_root' is missing in config file or invalid 'server_directory_root'.")
			sys.exit(1)

		if app_config['app_mode'] == 'client':
			if app_config['client_directory_root'] is None or not app_config['client_directory_root'] \
					or ' ' in app_config['client_directory_root']:
				logger.error("'client_directory_root' is missing in config file or invalid 'client_directory_root'.")
				sys.exit(1)
			if app_config['filename_ext'] is None:
				logger.error("'filename_ext' is missing in config file.")
				sys.exit(1)
			if app_config['server_hostname'] is None or not app_config['server_hostname'] \
					or ' ' in app_config['server_hostname']:
				logger.error("'server_hostname' is missing in config file or invalid 'server_hostname'.")
				sys.exit(1)
		elif not app_config['app_mode'] == 'server':
			logger.error("'app_mode' is Invalid!")
			sys.exit(1)

	except:
		raise


def create_logger(name):
	## Create logger
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.propagate = False
	return logger


def add_fh_to_logger(logger):
	## Add file hanlder to logger
	if sys.platform == 'win32':
		log_file_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '\logs\\ft-daemon.log'
	else:
		log_file_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/logs/ft-daemon.log'
	fh = logging.handlers.RotatingFileHandler(log_file_path, mode='a', maxBytes=10000000, backupCount=10)
	fh.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s'))
	fh.setLevel(logging.DEBUG)
	logger.addHandler(fh)
	keep_fds = [fh.stream.fileno()]
	return keep_fds


def create_dir_root(app_mode, dir_root_path):
	if app_mode == 'server' or app_mode == 'client':
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


def check_user(username, logger):
	"""This is for Linux or similar OS only"""
	output = subprocess.check_output('id -u ' + username + ' 2>/dev/null | wc -l', shell=True)
	if int(output) == 0:
		logger.info("User account for file transfer does not exist!\n"
		            "Please run 'ft-daemon.sh createuser' with root privilege (sudo) to create the user.")
		print("User account for file transfer does not exist!\n"
		      "Please run 'ft-daemon.sh createuser' with root privilege (sudo) to create the user.")
		return False
	else:
		output = subprocess.check_output('whoami', shell=True)
		if output == 'root':
			logger.warning("You are running ft-daemon as root which is not necessary and risky.")
			print("You are running ft-daemon as root which is not necessary and risky.")
			input = raw_input('Do you want to continue? [Y/n]: ')
			if input != "Y":
				return False
	return True


def create_user(username, passwd, dir_root_path, logger):
	"""This is for Linux or similar OS only"""
	output = subprocess.check_output('id -u ' + username + ' 2>/dev/null | wc -l', shell=True)
	if int(output) == 0:
		logger.info('User account for file transfer does not exist! Attempting to create it...')
		print('User account for file transfer does not exist! Attempting to create it...')
	else:
		logger.info('User account already exists! Exiting...')
		print('User account already exists! Exiting...')
		return 0

	# ret = os.system('which makepasswd 1>/dev/null')
	# if ret != 0:
	# 	logger.info('makepasswd utility is not found! Please install it first.')
	# 	print('makepasswd utility is not found! Please install it first.\n')
	# 	os._exit(2)

	uid = os.getuid()
	if int(uid) != 0:
		logger.info('Please re-run ft-daemon with root privilege (sudo) to create user for client to send files.')
		print('Please re-run ft-daemon with root privilege (sudo) to create user for client to send files.\n')
		os._exit(2)

	cmd = 'useradd -s /bin/bash %s && echo "%s:%s"|chpasswd' % (username, username, passwd)
	# print(cmd)
	if os.system(cmd) == 0:
		os.system('chgrp -R ' + username + ' ' + dir_root_path + '/incoming')
		logger.info('User account successfully created.')
		print('User account successfully created.')
	else:
		logger.info('Failed to create user account!')
		print('Failed to create user account!')
		os._exit(2)
	return 0


def module_exists(name):
	import imp
	try:
		imp.find_module('daemonize')
		found = True
	except ImportError:
		found = False
	return found


def isUserAdmin():
	if os.name == 'nt':
		import ctypes
		try:
			return ctypes.windll.shell32.IsUserAnAdmin()
		except:
			traceback.print_exc()
			print "Admin check failed, assuming not an admin."
			return False
	elif os.name == 'posix':
		# Check for root on Posix
		return os.getuid() == 0
	else:
		raise RuntimeError, "Unsupported operating system for this module: %s" % (os.name,)
