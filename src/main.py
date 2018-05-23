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
import time

__author__ = "Arun <hindol96[at]gmail.com>"


def get_params_for_daemonized_fn():
	global logger
	global app_config

	return logger, app_config


def main(argv):
	""" Main function """
	global app_config
	global logger

	USAGE = "\nUsage (in Linux):\n\tft-daemon.sh start|stop|createuser\n\nUsage (in Windows):\n\tft-daemon.bat start|stop\n"
	pid_file = "/tmp/ft-daemon.pid"

	try:
		if len(argv) < 1:
			print USAGE
			os._exit(1)

		action = argv[0]
		if sys.platform == 'win32':
			if action not in ['start','stop']:
				print USAGE
				os._exit(1)
		else:
			if action not in ['start','stop','createuser']:
				print USAGE
				os._exit(1)

		## Get confirmation
		if action == 'start' or action == 'createuser':
			input = raw_input("\nHave you configured config/ft-daemon.conf? [Y/n]: ")
			if input != 'Y':
				os._exit(1)

		## Create logger
		logger = create_logger('ft-daemon')

		## Parse config file parameters
		parse_config_file(logger)

		## Add file hanlder to logger
		keep_fds = add_fh_to_logger(logger)

		## For 'client' mode, check if rsync client application exists
		if app_config['app_mode'] == 'client':
			if action == 'createuser':
				logger.error("'createuser' is only valid if you are running ft-daemon in server mode\n")
				print("'createuser' is only valid if you are running ft-daemon in server mode\n")
				os._exit(2)

			## Create directory structure
			create_dir_root(app_config['app_mode'], app_config['client_directory_root'])

			## Compute file transfer app path
			ft_app_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/tools/pscp.exe'

			if sys.platform == 'win32':
				if not os.path.isfile(ft_app_path):
					logger.error(
						'File transfer tool (for client) cannot be found! Has it been removed from \'tools\' sub-directory?\n')
					sys.exit(2)

				win_client_path = os.path.dirname(os.path.realpath(__file__)) + '\win-client.py'
				if action == 'start':
					# test()
					ret = os.system('python %s --startup auto install' % win_client_path)
					if ret == 0:
						logger.info('serviced installed.')
						ret = os.system('python %s start' % win_client_path)
						if ret == 0:
							logger.info('ft-daemon service has been started.')
						else:
							logger.error('Failed to start ft-daemon service!')
					else:
						logger.error('Failed to install ft-daemon service!')
				else:
					logger.info('Stopping ft-daemon service...')
					ret = os.system('python %s stop' % win_client_path)
					if ret == 0:
						logger.info('ft-daemon service has been stopped.')
						ret = os.system('python %s remove' % win_client_path)
						logger.info('ft-daemon service has been removed.')
					else:
						logger.info('Failed to stop ft-daemon service!')

			else:
				from daemonize import Daemonize

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
					'ft-daemon does not support Windows in server mode.\n')
				os._exit(2)

			if action == 'createuser':
				output = subprocess.check_output("whoami|tr -d '\n'", shell=True)
				if output != 'root':
					print(output)
					logger.error("You need to run 'ft-daemon.sh createuser' as root or with sudo.")
					print("You need to run 'ft-daemon.sh createuser' as root or with sudo.")
					os._exit(2)
				else:
					create_user(app_config['server_username'], app_config['server_passwd'],
					            app_config['server_directory_root'], logger)
					os._exit(0)

			from daemonize import Daemonize

			## Create directory structure
			create_dir_root(app_config['app_mode'], app_config['server_directory_root'])

			## Create server user
			if check_user(app_config['server_username'], logger):
				os._exit(3)

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
		if not isUserAdmin():
			print('You need to run this application as administrator.')
			os._exit(1)

		## Install pywin32 module to create windows service
		if not module_exists('win32serviceutil'):
			ret = os.system('where pip')
			if ret != 0:
				os.system('python ../helper/get-pip.py')
			os.system('python -m pip install -U pip')

			## Install pywin32 module
			os.system('pip install pywin32')
			## Copy three necessary dlls to Python's installation root directory. Service does not start without this.
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
