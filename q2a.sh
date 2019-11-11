#!/bin/bash
cd ~/Q2A_Pi

#output time
date +"%d/%m/%Y %H:%M"

#update repository to last version
git fetch --all
git reset --hard origin/master

#set every file executable
chmod -R 777 ~/Q2A_Pi

#run script
./likes.py