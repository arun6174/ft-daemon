"""
File transfer daemon client functionality for Windows OS.
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from helper import *
import shutil
import time

__author__ = "Arun <hindol96[at]gmail.com>"

class AppServerSvc (win32serviceutil.ServiceFramework):
	_svc_name_ = "ft-daemon"
	_svc_display_name_ = "File transfer service"
	stopService = False

	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.hWaitStop = win32event.CreateEvent(None,0,0,None)
		socket.setdefaulttimeout(60)

	def SvcStop(self):
		self.stopService = True
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)

	def SvcDoRun(self):
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
							  servicemanager.PYS_SERVICE_STARTED,
							  (self._svc_name_,''))
		self.main()

	def main(self):
		## Create logger and add file handler to it
		logger = create_logger('ft-daemon')
		keep_fds = add_fh_to_logger(logger)

		try:
			## Parse config file parameters
			parse_config_file('../config/ft-daemon.conf')

			## Relevant directories
			source_dir = app_config['client_directory_root'] + '\\new'
			insync_dir = app_config['client_directory_root'] + '\\in-sync'
			archive_dir = app_config['client_directory_root'] + '\\archived'

			## Get full path for file transfer tool
			ft_app_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '\\tools\\pscp.exe'

			## Get allowed filename extensions
			filename_exts = [x.strip() for x in app_config['filename_ext'].split(',')]

			logger.info(__file__ + ': ft-daemon service started')
			last_checked_time = 0
			while not self.stopService:
				if (int(time.time()) - last_checked_time < 10):
					continue

				## check if any new file(s) exist in source dir and if they haven't
				## been modified in last 1 minute, then move them to destination (in-sync) subdir.
				for filename in os.listdir(source_dir):
					extension = os.path.splitext(filename)[1]
					if extension in filename_exts:
						mtime = os.path.getmtime(source_dir + '/' + filename)
						curr_time = int(time.time())
						if (curr_time - mtime > 30):
							name = os.path.splitext(filename)[0]
							shutil.move(source_dir + '/' + filename,
							            insync_dir + '/' + name + '_' + str(int(mtime)) + extension)
						continue
					else:
						continue

				## Check if ft app exists
				if not os.path.isfile(ft_app_path):
					logger.critical(
						'File transfer tool (for client) cannot be found! Has it been removed from \'tools\' sub-directory?')
					sys.exit(3)

				server_dir = app_config['server_directory_root'] + '/incoming'

				## Send files in 'in-sync' subdir to server's appropriate dir.
				for filename in os.listdir(insync_dir):
					if sys.platform == 'win32':
						filepath = insync_dir + '/' + filename
						filesize = str(int(os.path.getsize(filepath) / 1000)) + 'KB'
						cmd = "echo y | %s -l %s -pw %s %s %s:%s" % (
							ft_app_path, app_config['server_username'], app_config['server_passwd'], filepath,
							app_config['server_hostname'], server_dir)
						output = os.system(cmd)
						if (int(output) != 0):
							logger.error('Failed to send %s to server! Error code = %d' % (filepath, int(output)))
						else:
							logger.info('%s (%s) successfully sent to server at %s' % (filepath, filesize, server_dir))
							shutil.move(filepath, archive_dir + '/' + filename)
							logger.info('Moved %s from %s to %s' % (filename, insync_dir, archive_dir))

				last_checked_time = int(time.time())
				time.sleep(2)

		except:
			traceback.print_exc(file=sys.stdout)
			logger.exception('Got following exception in ' + __file__)
		finally:
			logger.info(__file__ + ': ft-daemon service stopped')


if __name__ == '__main__':
	win32serviceutil.HandleCommandLine(AppServerSvc)
