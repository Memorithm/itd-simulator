"""Prospective ITD Pascal R4 non-final source and geometry contracts."""

from __future__ import annotations

from itd_research.experiment_schema import SplitRole

PASCAL_R4_VERSION = "itd-pascal-r4-interruption-resume-v1"
PASCAL_R4_PREFIXES = (1, 4, 7)
PASCAL_R4_CASES_PER_SPLIT = 8
_GATE_COUNT = 8
_DENSITY = 11


def pascal_r4_shape(role: SplitRole) -> tuple[int, int]:
    resolved = SplitRole(role)
    if resolved is SplitRole.FINAL:
        raise ValueError("Pascal R4 final source is protected and not authorized.")
    return (7, 128) if resolved is SplitRole.DEVELOPMENT else (9, 512)


def pascal_r4_case_ids(role: SplitRole) -> tuple[str, ...]:
    resolved = SplitRole(role)
    n, _ = pascal_r4_shape(resolved)
    prefix = "dev" if resolved is SplitRole.DEVELOPMENT else "val"
    return tuple(f"{prefix}-n{n}-case-{index:02d}" for index in range(PASCAL_R4_CASES_PER_SPLIT))


def pascal_r4_source_payload(role: SplitRole) -> bytes:
    """Return exact little-endian packed-u16 non-final source bytes."""

    n, domain_size = pascal_r4_shape(role)
    table = [0] * domain_size
    constants = 0
    for gate in range(_GATE_COUNT):
        if gate % 3 == 1:
            constants |= 1 << gate
        terms = tuple(
            1 + ((17 * gate + 31 * index) % (domain_size - 1))
            for index in range(_DENSITY)
        )
        if len(set(terms)) != _DENSITY:
            raise ValueError("Pascal R4 generator produced duplicate terms.")
        lane = 1 << gate
        for term in terms:
            table[term] ^= lane
    table[0] = constants
    for bit in range(n):
        selector = 1 << bit
        for mask in range(domain_size):
            if mask & selector:
                table[mask] ^= table[mask ^ selector]
    return b"".join(word.to_bytes(2, "little", signed=False) for word in table)
