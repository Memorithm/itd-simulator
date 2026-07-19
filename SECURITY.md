# Security policy

## Supported versions

| Version | Security support |
|---|---|
| 0.2.x source / ITD V29.18 | Current |
| 0.1.1 / V10 | Historical; no routine fixes |
| Earlier scientific snapshots | Historical; no routine fixes |

There is no guarantee of a response SLA. This is a research prototype, not a
safety-critical or production control system.

## Reporting a vulnerability

GitHub private vulnerability reporting is not currently enabled for this
repository. Do not publish exploit details, credentials, private paths, or
sensitive data in a public issue. Open a minimal public issue asking the owner
to establish a private reporting channel, without technical exploit detail.
The owner should enable GitHub private vulnerability reporting as a repository
setting; that external setting is not changed by source commits.

For a non-sensitive robustness bug, open a normal issue with the version,
commit, environment, minimal input, and observed impact.

## Scope

Relevant reports include unsafe output-path behavior, unintended overwrites,
path traversal, dependency vulnerabilities, denial-of-service amplification,
unbounded entrypoint resource use, unexpected global state, and malformed input
that bypasses documented validation. Claims about the scientific validity of
the experimental model are important research feedback but are not security
vulnerabilities by themselves.

Do not run the simulator on untrusted Python modules or field callables: they
are executable code with the process's privileges. The core imposes no
arbitrary array-size limit; applications exposed to untrusted requests must
enforce explicit memory, CPU, timeout, and output quotas at their boundary.
