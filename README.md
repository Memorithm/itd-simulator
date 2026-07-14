# ITD Simulator

Deterministic research simulator for curvature-weighted rotational
intensity and structural dynamics.

## Version

Current release: 0.1.1

## Main outputs

The simulator computes:

1. curvature-weighted rotational intensity;
2. a five-component structural signature;
3. an optional scalar score using explicit normalized weights.

The structural components are:

- heterogeneity;
- localization;
- roughness;
- sign mixing;
- temporal deformation.

## Installation

Create a Python virtual environment, activate it, then install the
dependencies listed in requirements.txt.

Commands:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

## Run

    python itd_v10.py

## Validate

    ./run_validation.sh

## Release integrity

Official archive SHA-256:

    af323367f804853ebf980e0805d2127714b7f5971abb3d0848d375b4931ba00e

## Scientific status

This project is a mathematical and numerical research prototype.

Its tests establish internal numerical and software consistency. They
do not establish the ITD as a validated physical observable, a universal
measure of complexity, an entropy, or a replacement for Shannon
information theory.

## Licence

No software licence has yet been selected. Public visibility alone does
not grant permission to copy, modify, redistribute, or commercially
reuse the source.
