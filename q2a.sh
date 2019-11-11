#!/bin/bash
cd ~/Uniroma3_Feed

#update to git last version
git fetch --all
git reset --hard origin/master

#set every file executable
chmod -R 777 ~/Uniroma3_Feed

#run script
date +"%d/%m/%Y %H:%M" > log.txt
./main.py >> log.txt