#!/usr/bin/env bash
# Ben Chapman-Kish
# 2016-09-03

# In order for this script to work, git must be configured
# to connect with ssh, and the ssh key must be kept in a
# local, loaded keychain (e.g. with ssh-add)

git pull origin master
python3 superbot.py
PID_FILE=$(cat superbot_pid_file.txt)
while true; do
	git fetch origin
	NUM_DIFF=$(git rev-list HEAD...origin/master --count)
	if [[ ! "$NUM_DIFF" -eq 0 ]]; then
		kill $(cat PID_FILE)
		git merge origin/master
		python3 superbot.py
		PID_FILE=$(cat superbot_pid_file.txt)
	fi
	sleep 10
done