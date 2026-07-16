#!/usr/bin/env bash

cd "$HOME/itd-simulator" || {
    echo "ERREUR : impossible d'ouvrir $HOME/itd-simulator"
    exit 1
}

source .venv/bin/activate || {
    echo "ERREUR : environnement virtuel absent"
    exit 1
}

exec python tools/finish_v29_series.py "$@"
