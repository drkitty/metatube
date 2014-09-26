#!/usr/bin/env bash

for f in requirements/*; do
    pip2 install -r "$f"
done
