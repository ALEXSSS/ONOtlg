#!/bin/bash

set -e

python3 -m venv ono_venv
source ono_venv/bin/activate

sudo apt-get install python3.7-dev
pip3 install psycopg2-binary
pip3 install pytelegrambotapi
pip3 install telethon
pip3 install nltk
