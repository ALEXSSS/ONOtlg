#!/bin/bash

PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONPATH

source ono_venv/bin/activate
nohup python3 extractor/extractor.py > nohup_extractor.log &