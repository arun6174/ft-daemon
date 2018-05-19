#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a controller application for file syncing between two computers, where one computer
acts as client and the other acts as server. This application can be executed either in
server or client mode. The application when started runs as a daemon/detached process, which
can be killed from console (in Linux) or from Task manager (in Windows). It also gets killed
when computer reboots or shuts down and doesn't start automatically.
"""

# import getopt
from helper import *
import client
import server
import shutil

__author__ = "Arun <aghose@i2r.a-star.edu.sg>"


def get_params_for_daemonized_fn():
	global logger
	global app_config

	return logger, app_config


def main(argv):
	from daemonize import Daemonize

	""" Main function """
	global app_config
	global logger

	pid_file = "/tmp/ft-daemon.pid"

	try:

		if len(argv) < 1:
			print '\nUsage (in Linux):\n\tft-daemon.sh start|stop\nUsage (in Windows):\n\tft-daemon.bat start|stop'
			sys.exit(1)

		action = argv[0]
		if action not in ['start','stop']:
			print '\nUsage (in Linux):\n\tft-daemon.sh start|stop\nUsage (in Windows):\n\tft-daemon.bat start|stop'
			sys.exit(1)

		## Create logger
		logger = create_logger('ft-daemon')

		## Parse config file parameters
		parse_config_file('../config/ft-daemon.conf', logger)

		## Add file hanlder to logger
		keep_fds = add_fh_to_logger(logger)

		## For 'client' mode, check if rsync client application exists
		if app_config['app_mode'] == 'client':
			## Create directory structure
			create_dir_root(app_config['app_mode'], app_config['client_directory_root'])

			## Compute file transfer app path
			ft_app_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/tools/pscp.exe'

			if sys.platform == 'win32':
				if not os.path.isfile(ft_app_path):
					logger.error(
						'File transfer tool (for client) cannot be found! Has it been removed from \'tools\' sub-directory?')
					sys.exit(2)

				if action == 'start':
					ret = os.system('python win-client.py --startup auto install')
					if ret == 0:
						ret = os.system('python win-client.py start')
						if ret == 0:
							logger.info('ft-daemon service has been started.')
						else:
							logger.error('Failed to start ft-daemon service!')
					else:
						logger.error('Failed to install ft-daemon service!')
				else:
					ret = os.system('python win-client.py stop')
					if ret == 0:
						logger.info('ft-daemon service has been stopped.')
						ret = os.system('python win-client.py remove')
					else:
						logger.info('Failed to stop ft-daemon service!')

			else:
				if action == 'start':
					daemon = Daemonize(app="ft-daemon-client", pid=pid_file, action=client, keep_fds=keep_fds, logger=logger,
					                   privileged_action=get_params_for_daemonized_fn)
					daemon.start()
					pid = subprocess.check_output('cat ' + pid_file, shell=True)
					logger.info('ft-daemon has been started in client mode. pid = ' + pid)
				else:
					os.system('kill -9 `cat %s`' % pid_file)
					logger.info('ft-daemon has been stopped.')

		## For 'server' mode, check if ft-daemon user a/c exists. Create it if it doesn't exist
		else:
			if (sys.platform == 'win32'):
				logger.error(
					'You are tying to run ft-daemon in server mode in a Windows machine. '
					'ft-daemon does not support Windows in server mode.')
				sys.exit(2)

			## Create directory structure
			create_dir_root(app_config['app_mode'], app_config['server_directory_root'])

			## Create server user
			create_user(app_config['server_username'], app_config['server_passwd'], app_config['server_directory_root'])

			if action == 'start':
				## Start server daemon
				daemon = Daemonize(app="ft-daemon-server", pid=pid_file, action=server, keep_fds=keep_fds, logger=logger,
				                   privileged_action=get_params_for_daemonized_fn)
				daemon.start()
				pid = subprocess.check_output('cat ' + pid_file, shell=True)
				logger.info('ft-daemon has been started in server mode. pid = ' + pid)
			else:
				os.system('kill -9 `cat %s`' % pid_file)
				logger.info('ft-daemon has been stopped.')


	except:  ## catch *all* exceptions
		traceback.print_exc(file=sys.stdout)
		logger.exception('Got following exception in main')
	finally:
		sys.exit()  ## Exit app


if __name__ == "__main__":

	if sys.platform == 'win32':
		ret = os.system('where pip')
		if ret != 0:
			os.system('python ../helper/get-pip.py')
		os.system('python -m pip install -U pip')

		## Install pywin32 module to create windows service
		if not module_exists('win32serviceutil'):
			os.system('pip install pywin32')
			## Copy three necessary dlls to Python's installation root directory
			## Service does not start without this.
			for f in os.listdir('C:\Python27\Lib\site-packages\pywin32_system32'):
				shutil.move(f, 'C:\Python27')

	else:
		if not module_exists('daemonize'):
			print 'Python package daemonize not found. Installing... Please wait.'
			## Install pip if not installed
			ret = os.system('which pip')
			if ret != 0:
				os.system('python ../helper/get-pip.py')
			os.system('pip install -U pip')

			os.system('pip install daemonize')



	main(sys.argv[1:])
