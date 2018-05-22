# ft-daemon

A cross-platform daemon/service for automatic file transfer from a sender to a receiver computer.

<br>

-------------
What's this?
-------------

ft-daemon is a file transfer daemon tool which facilitates automatic file transfer
between two computers.

Some of its key features:

  - It can transfer files between two computers in the same network or the sender
    can be behind a NAT/firewall and receiver can be on the Internet.

  - It's an uni-directional file transfer tool. It only allows sender to send files
    to receiver, not the other way.

  - It runs either in client (sender) or server (receiver) mode.

  - It's developed using Python 2.7, so a Python 2.7 installation is necessary
    in both sender and receiver.

  - As of now, it supports Windows only as a client/sender, not as a server/receiver.
  
<br>

------------------
How does it work?
------------------

The tool was created to serve a certain use-case where a computer wants to
automatically and periodically send any type of file (binary or text) to another
computer.

The assumption in the use-case is that the sender is constantly and periodically
generating file(s) which it wants to send to receiver for some sort of processing.
Once a file is sent, it should never be sent again.

It maintains following directory hierarchy in sender and receiver:

    client-directory-root           server-directory-root
        |                               |
        |--- new                        |--- incoming
        |                               |
        |--- in-sync                    |--- for-processing
        |                               |
        |--- archived                   |--- processed

Whatever file(s) Sender is generating and wants to send to receiver, it must put
the file inside *client-directory-root/new*. ft-daemon periodically (every 10 sec)
checks whether there is any file inside *client-directory-root/new* and whether the
last modified time of the file(s) is more than 1 minute. If so, it first moves the 
file to *client-directory-root/in-sync*. Then ft-daemon transmits the file to server 
to it's server-directory-root/in-coming directory. Once successfully sent, the file 
is then moved from from *client-directory-root/in-sync* to *client-directory-root/archived*.

ft-daemon, that is running in receiver, periodically (every 10 sec) checks whether
there is any new file in server-directory-root/in-coming directory and whether the
last modified time of the file(s) is more than 30 seconds. If so, it moves the file(s)
to server-directory-root/for-processing directory.

Once the file(s) in *server-directory-root/for-processing* directory are processed,
receiver computer should move then out of from there to avoid unnecessary confusion.
After processing, the file(s) can be moved to *server-directory-root/processed* directory.

Instead of using root account or the user account ft-daemon is running under in server,
ft-daemon creates a special account (username and password is configurable) in server
for client to connect and send files. This account does not have it's own home directory
and has read-write access only to *server-directory-root/in-coming* directory.


<br>

-----------------
How do I use it?
-----------------

#### On Server:

To setup the whole system of automatic transfer, you first need to configure and start
ft-daemon in the server/receiver computer.

As of now, 'server' mode is only supported for Linux. You need to fill in or update
necessary parameters in *confg/ft-daemon.conf* file. Change 'app_mode' to 'server'.
Update 'server_directory_root' - put appropriate value inside <>. Put a strong password
for 'server_passwd' which client/sender uses to send files.

Once config file is ready, execute ft-daemon.sh as follows:

  - To start the daemon:

        ft-daemon.sh start

  - To stop the daemon:

        ft-daemon.sh stop

It prints out necessary logs and will guide you through. Once the daemon is running,
you can check the logs in logs/ sub-directory.


#### On Client:

Now, move to the sender/client computer and update ft-daemon.conf appropriately. Change
'app_mode' to 'client'. Set 'filename_ext' to appropriate filename extension(s). Update 
both 'client_directory_root', 'server_directory_root' and 'server_hostname'. Make user 
the value of 'server_directory_root' matches the value you put for server side ft-daemon. 
Use the same 'server_username' and 'server_passwd' you used for server side config.

Once config file is ready in client/sender computer, execute ft-daemon.bat or ft-daemon.sh
file from command line depending on your OS.

  - To start the daemon:

        ft-daemon.bat start

  - To stop the daemon:

        ft-daemon.bat stop

It shows necessary logs and will guide you through. Once the daemon is running, you can check the
logs in logs/ sub-directory.

**Notes:** If you are running the client in a **Windows** machine, you need to run the batch
script in _administrator_ mode. Right-click on 'Command Prompt' icon in Start menu and click 
'Run as administrator' to open command prompt in administrator mode. You should run the batch
script from there.


<br>

--------------
Special notes
--------------

In client/sender, whatever application is generating the file(s), for sending to server,
it must create a new file every time. It should not open a file for a very long time and
keep updating it. It can either move the file when ready to *client-directory-root/new* directory
or it can directly create and save the file in that directory. If the application is directly
creating the file in that directory, it must not keep the file open and edit after long intervals.
ft-daemon attempts to move file(s) from that directory whose last modified time is more than 30 
seconds. If the file(s) are locked by an application, ft-daemon may simply fail to move them to 
'in-sync' sub-directory and the file(s) will not be sent to server until the lock is released.