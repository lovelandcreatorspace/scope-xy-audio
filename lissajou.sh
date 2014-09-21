#!/bin/bash

cd `dirname $0`
exec ./lissajou.py | aplay /dev/stdin
