#!/bin/bash
DIR=plugin.video.espn_3
cd ..
rsync -av --copy-links --delete $DIR /mnt/storage/development/repo-plugins/ \
 --exclude "*.pyo" --exclude "*.pyc" --exclude ".git" --exclude ".idea" \
 --exclude "*.sh" --exclude "bugs" --exclude ".*" --exclude "TODO" \
 --exclude "README.md" --exclude "test" --exclude "Pipfile*"
