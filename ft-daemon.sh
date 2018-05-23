#!/bin/bash
action=$1
if [ "$action" != "start" -a "$action" != "stop" -a "$action" != "createuser" ]; then
    echo "Usage: $0 <start|stop|createuser>"
    exit 1
fi

[ -z "$(which python2.7)" ] && {
    echo "Python 2.7 is not installed im the system."
    echo "Install Python 2.7 and try again."
    exit 1
}

my_dir="`dirname "$0"`"
python2.7 $my_dir/src/main.py "$1"

