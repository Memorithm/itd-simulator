# Scientific definition — ITD V29.18

## Scope

ITD V29.18 is an experimental numerical construction over a two-dimensional
velocity field. The definitions below describe what the code computes; they do
not assert a universal physical observable or information measure.

Let the sampled velocity be

\[
\mathbf{v}(x,y,t)=(v_x,v_y), \qquad
\omega=\partial_xv_y-\partial_yv_x.
\]

Let \(R(x,y,t)\) be the supplied curvature-like scalar field and \(\ell_c\)
the characteristic length. The exponential requires \(\ell_c^2R\) to be
dimensionless. For dimensional coordinates this normally means
\([R]=L^{-2}\); the bundled synthetic field is a numerical test field and is
not derived from a physical metric.

## Curvature-weighted rotational intensity

The instantaneous rate is

\[
I(t)=\left\langle \omega^2
\exp\!\left(\ell_c^2R\right)\right\rangle_\Omega,
\]

where \(\langle\cdot\rangle_\Omega\) is the boundary-mode-dependent spatial
mean. The reported index is the observed-duration average

\[
\bar I=\frac{1}{t_N-t_0}\int_{t_0}^{t_N} I(t)\,dt.
\]

If velocity has dimensions \(L/T\), then \(\omega\) has \(T^{-1}\) and
\(I\) and \(\bar I\) have \(T^{-2}\). No normalization makes intensity
comparable across unrelated unit systems automatically.

## Five-component structural signature

Write \(A=|\omega|\), \(\omega_{\rm rms}=\sqrt{\langle\omega^2\rangle}\),
and let \(\varepsilon=10^{-12}\) be the numerical zero threshold. The raw
components are:

1. Heterogeneity

   \[
   H=\frac{\sqrt{\langle(A-\langle A\rangle)^2\rangle}}
           {\max(\langle A\rangle,\varepsilon)}.
   \]

2. Localization

   \[
   L=\frac{\langle\omega^4\rangle}
           {\max(\langle\omega^2\rangle^2,\varepsilon)}-1.
   \]

3. Roughness at structural length \(\ell_s\)

   \[
   Q=\ell_s\frac{\langle\sqrt{(\partial_x\omega)^2+
   (\partial_y\omega)^2}\rangle}
   {\max(\omega_{\rm rms},\varepsilon)}.
   \]

4. Sign mixing

   \[
   M=\operatorname{clip}\!\left(
   1-\frac{|\langle\omega\rangle|}
   {\max(\langle|\omega|\rangle,\varepsilon)},0,1\right).
   \]

5. Eulerian temporal deformation on interval \([t_{i-1},t_i]\)

   \[
   D_i=\frac{\sqrt{\langle(\omega_i-\omega_{i-1})^2\rangle}}
   {\Delta t_i\,\tfrac12(\omega_{{\rm rms},i}+
   \omega_{{\rm rms},i-1})}.
   \]

The first four are dimensionless when \(\ell_s\) shares the coordinate length
unit. As implemented, \(D_i\) has inverse-time dimensions unless time was
nondimensionalized beforehand. Consequently, changing the time unit can change
the scalar aggregation. This is an explicit numerical limitation, not a hidden
claim of unit invariance.

For a numerically zero vorticity field, all five components and the structural
score are defined as zero.

## Optional scalar aggregation

For \(x\ge0\), define \(b(x)=x/(1+x)\). Nonnegative weights are normalized so
\(\sum_k w_k=1\), then

\[
S= w_Hb(H)+w_Lb(L)+w_Qb(Q)+w_MM+w_Db(D).
\]

The four nodal spatial components are averaged to each time interval; temporal
deformation already belongs to an interval. Component indices and \(S\) are
duration-weighted interval averages. The default weights are equal.

This scalar score is experimental and preference-dependent. Reporting the
five-component vector and its weights is necessary for interpretation. The
additional coupled diagnostic

\[
C_i=I_i(1+S_i)
\]

is also experimental and does not replace the independent intensity and
structure axes.

## Eulerian and material deformation

The standard component compares vorticity at fixed grid nodes. Optional
periodic transport compensation first semi-Lagrangianly transports the previous
field to the current nodes and compares against that transported field.

A separate material diagnostic evaluates

\[
\frac{D\omega}{Dt}=\frac{\partial\omega}{\partial t}
+\mathbf{u}\cdot\nabla\omega
\]

with interval-centered vorticity and advection velocity. Its Eulerian,
advective, and material RMS rates are reported independently; norms of the
terms are not additive. This material diagnostic is not injected into the
five-component signature automatically.

## Multiscale and reference frames

The multiscale profile evaluates different \(\ell_s\) values. Raw roughness is
exactly linear in \(\ell_s\) in this implementation; other raw components are
unchanged, while bounding makes the final scalar response nonlinear.

Orthogonal rotations/reflections use \(Q^Tx\) for scalar source coordinates and
\(Qv(Q^Tx,t)\) for vectors. Galilean transformations use translated source
coordinates and subtract frame velocity from transformed velocity. Spatial
scaling transforms coordinates, velocity, curvature, and declared lengths
according to the explicit helper contracts. Discrete interpolation, finite
boundaries, and truncation can prevent exact numerical covariance.

## Interpretation limits

The implementation contains no empirical calibration to a physical experiment,
no statistical population model, and no proof of uniqueness or universality.
ITD does not replace entropy, Shannon information, physical observables, or
established complexity measures. Certification means agreement with specified
analytical cases, regression references, environments, and tolerances only.
