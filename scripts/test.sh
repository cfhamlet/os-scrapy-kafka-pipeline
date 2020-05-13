#!/bin/sh -e

set -x

pip install -r requirements/requirements-test.txt

tox