#!/bin/sh
# Korumayi bu klonda etkinlestirir. Klon basina bir kez kosulur.
set -e
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push tools/sir_kapisi.py
echo "sir-kapisi kuruldu: core.hooksPath=.githooks"
