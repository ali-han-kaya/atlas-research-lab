#!/bin/sh
# Korumayi bu klonda etkinlestirir. Klon basina bir kez kosulur.
set -e
git config core.hooksPath .githooks
if [ -f tools/sir_kapisi.py ]; then
  chmod +x .githooks/pre-commit .githooks/pre-push tools/sir_kapisi.py
else
  chmod +x .githooks/pre-commit .githooks/pre-push scripts/sir_kapisi.py
fi
echo "sir-kapisi kuruldu: core.hooksPath=.githooks"
