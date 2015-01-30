#!/usr/bin/env bash

for f in requirements/*; do
    pip2 install -Ur "$f"
done
