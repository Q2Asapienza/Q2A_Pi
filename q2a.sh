#!/bin/bash
cd ~/Q2A_Pi

#update to git last version
git fetch --all
git reset --hard origin/master

#set every file executable
chmod -R 777 ~/Q2A_Pi

#run script
date +"%d/%m/%Y %H:%M"
./likes.py