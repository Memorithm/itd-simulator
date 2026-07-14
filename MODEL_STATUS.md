# ITD Simulator — Model status

## Version

0.1.1 — corrected autonomous release of the V10 research prototype.

## Primary outputs

The simulator returns:

1. curvature-weighted rotational intensity;
2. a five-component structural signature;
3. an optional scalar structural score based on explicit normalized weights.

The structural components are:

- heterogeneity;
- localization;
- roughness;
- sign mixing;
- temporal deformation.

## Validated software properties

- calm, coherent-vortex and multi-vortex classification;
- vector-signature reconstruction;
- explicit normalized structural weights;
- one-component and arbitrary weighted combinations;
- rejection of invalid structural weights;
- autonomous execution without earlier ITD source versions.

## Scientific limitation

These tests establish internal mathematical and numerical consistency.
They do not establish that the ITD is a validated physical observable,
an entropy replacement, or a universal measure of complexity.
