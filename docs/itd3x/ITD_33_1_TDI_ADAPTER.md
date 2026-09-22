# ITD-33.1 — TDI adaptive-inference trajectory adapter

Status: **implementation slice active**

## Upstream boundary

TDI-9.x owns adaptive-inference semantics. Its current programme defines C0 fixed compute, C1 static preallocation, C2 adaptive stopping and C3 adaptive verification/recovery. TDI-9.1 is still only partially frozen and TDI-9.2 does not yet exist as a runnable final surface.

ITD therefore must not invent missing TDI observation fields.

## Adapter strategy

`TdiTrajectoryStepRef` carries an opaque non-final TDI snapshot identity:

- trajectory and step identity;
- Development or Validation split role only;
- TDI-9.1 or TDI-9.3 non-final stage;
- C0/C1/C2/C3 policy arm;
- exact TDI source identity;
- upstream observation-schema identifier;
- payload SHA-256;
- optional declared TDI action.

## Action consistency

The adapter enforces current TDI policy semantics at the boundary:

- C0/C1 cannot report adaptive VERIFY/BACKTRACK/RECOVER actions;
- C2 cannot report VERIFY/BACKTRACK/RECOVER;
- C3 may carry recovery/verification actions.

## Structural descriptors

`TdiStructuralDescriptorRecord` attaches an ITD-33 research descriptor to the opaque TDI step while retaining a separate ITD source identity and descriptor semantics.

This prevents an ITD measurement from being confused with a native TDI observable.

## Transition pairs

`TdiTrajectoryPair` requires causal step ordering plus identical TDI source, observation schema and stage.

## Explicit exclusions

- no TDI-9.2 final adapter;
- no access to protected final material;
- no invented unresolved TDI-9.1 fields;
- no automatic stopping or recovery policy;
- no reinterpretation of TDI evidence.
