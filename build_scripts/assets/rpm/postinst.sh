#!/usr/bin/env bash
# Post install script for the UI .rpm to place symlinks in places to allow the CLI to work similarly in both versions

set -e

ln -s /usr/lib/chives-blockchain/resources/app.asar.unpacked/daemon/chives /usr/bin/chives || true
ln -s /usr/lib/chives-blockchain/resources/app.asar.unpacked/daemon /opt/chives || true
