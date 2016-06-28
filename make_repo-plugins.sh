#!/bin/bash
DIR=plugin.video.espn_3
cd ..
rsync -av --copy-links --delete $DIRx repo-plugins/plugin.video.espn_3/ --exclude "*.pyo" --exclude "*.pyc" --exclude ".git" --exclude ".idea" --exclude "*.sh" --exclude "bugs" --exclude ".*" --exclude "TODO"

