#!/usr/bin/env python3
"""Offline strategy validation only; never authorizes or executes a campaign."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

OWNERS = {'ITD', 'SciRust', 'SML-GENIUS', 'FLAT-ATTENTION', 'ElasticXxx', 'NoiseLab', 'Forge'}
STATES = {'planned', 'active', 'blocked', 'completed'}
AUTHORITY = {'final_holdout_access', 'runtime_actuation', 'model_promotion', 'automatic_merge'}
ID = re.compile(r'(?:ITD-3[0-9]\.[0-9]+|V888-(?:BOOL-[0-9]+\.[0-9]+|DATA-[0-9]+|GROWTH-[0-9]+))\Z')
SHA = re.compile(r'[0-9a-f]{40}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        require(key not in obj, f'duplicate JSON key: {key}')
        obj[key] = value
    return obj


def load(path: Path) -> dict:
    require(path.stat().st_size <= 1024 * 1024, 'programme exceeds 1 MiB')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)


def validate(p: dict) -> list[str]:
    """Check internal consistency, not truth of supplied external evidence."""
    require(isinstance(p, dict), 'programme must be an object')
    expected = {'schema_version', 'programme', 'revision', 'observed_on', 'owner',
                'execution_host', 'implementation_language', 'frozen_model',
                'raw_data_external', 'authority', 'issue', 'source_scope', 'families',
                'milestones', 'first_functional_target', 'next_implementation'}
    require(set(p) == expected, 'unknown or missing programme fields')
    require(type(p['schema_version']) is int and p['schema_version'] == 1, 'unsupported schema')
    require(p['programme'] == 'ITD3X-V888-BOOL-GROWTH', 'unexpected programme')
    require(nonempty(p['revision']), 'revision is required')
    require(isinstance(p['observed_on'], str), 'observed_on must be a date')
    require(date.fromisoformat(p['observed_on']).isoformat() == p['observed_on'], 'noncanonical date')
    require(p['owner'] == 'Memorithm/itd-simulator', 'unexpected programme owner')
    require(p['execution_host'] == 'Thor', 'execution host must remain Thor')
    require(p['implementation_language'] == 'Rust', 'execution implementation must remain Rust')
    require(p['frozen_model'] == 'ITD V29.18', 'frozen model must remain unchanged')
    require(p['raw_data_external'] is True, 'raw data must stay external')
    require(isinstance(p['authority'], dict) and set(p['authority']) == AUTHORITY,
            'authority fields must be explicit')
    require(all(v is False for v in p['authority'].values()), 'roadmap grants no authority')
    require(type(p['issue']) is int and p['issue'] > 0, 'tracking issue is required')
    source = p['source_scope']
    require(isinstance(source, dict), 'source scope must be an object')
    require(source.get('dataset') == 'BANC' and source.get('materialization') == 'v888'
            and source.get('detector') == 'v3', 'source scope changed without protocol revision')
    require(isinstance(source.get('raw_synapse_sha256'), str)
            and bool(DIGEST.fullmatch(source['raw_synapse_sha256'])), 'invalid source digest')
    for key in ('raw_synapse_bytes', 'raw_synapse_rows', 'metadata_nodes',
                'edgelist_pairs', 'induced_synapse_contacts'):
        require(type(source.get(key)) is int and source[key] > 0, f'invalid count: {key}')
    require(source['induced_synapse_contacts'] <= source['raw_synapse_rows'], 'invalid induced scope')
    require(nonempty(source.get('verified_scope')), 'verification scope is required')
    families = p['families']
    require(isinstance(families, list) and len(families) == 10, 'preserve ten ITD-3X families')
    require(all(isinstance(f, dict) and set(f) == {'id', 'name', 'issue'} for f in families),
            'invalid family record')
    require({f['id'] for f in families} == {f'ITD-{i}.x' for i in range(30, 40)},
            'missing or duplicate ITD family')
    require(all(nonempty(f['name']) and type(f['issue']) is int and f['issue'] > 0
                for f in families), 'invalid family description/issue')
    stages = p['milestones']
    require(isinstance(stages, list) and 0 < len(stages) <= 1000, 'invalid milestone count')
    lookup = {}
    keys = {'id', 'title', 'itd_series', 'owner', 'status', 'depends_on', 'exit_criteria', 'evidence'}
    for s in stages:
        require(isinstance(s, dict) and set(s) == keys, 'invalid milestone fields')
        sid = s['id']
        require(isinstance(sid, str) and bool(ID.fullmatch(sid)), 'invalid milestone ID')
        require(sid not in lookup, f'duplicate milestone: {sid}')
        require(nonempty(s['title']) and s['owner'] in OWNERS, 'missing title or unknown owner')
        require(s['itd_series'] in {f['id'] for f in families}, 'unknown ITD mapping')
        require(s['status'] in STATES, 'unknown lifecycle status')
        require(isinstance(s['depends_on'], list) and all(nonempty(x) for x in s['depends_on']),
                'dependencies must be strings')
        require(len(s['depends_on']) == len(set(s['depends_on'])), 'duplicate dependency')
        require(isinstance(s['exit_criteria'], list) and s['exit_criteria']
                and all(nonempty(x) for x in s['exit_criteria']), 'missing exit criteria')
        require(isinstance(s['evidence'], list), 'evidence must be a list')
        if s['status'] == 'completed':
            require(bool(s['evidence']), 'completion without evidence')
        for e in s['evidence']:
            require(isinstance(e, dict) and set(e) == {'url', 'source_commit', 'scope'},
                    'invalid evidence record')
            require(isinstance(e['url'], str) and e['url'].startswith('https://github.com/'),
                    'evidence must have a GitHub source URL')
            require(isinstance(e['source_commit'], str) and bool(SHA.fullmatch(e['source_commit'])),
                    'evidence needs an exact source commit')
            require(nonempty(e['scope']), 'evidence scope is required')
        lookup[sid] = s
    for s in stages:
        require(all(d in lookup for d in s['depends_on']), f'unknown dependency: {s["id"]}')
        require(s['id'] not in s['depends_on'], 'self dependency')
        if s['status'] == 'completed':
            require(all(lookup[d]['status'] == 'completed' for d in s['depends_on']),
                    'completed milestone has incomplete dependency')
    remaining = {s['id']: set(s['depends_on']) for s in stages}
    order = []
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if not deps)
        require(bool(ready), 'dependency cycle')
        order.extend(ready)
        for k in ready:
            del remaining[k]
        for deps in remaining.values():
            deps.difference_update(ready)
    require(p['first_functional_target'] in lookup, 'unknown functional target')
    require(p['next_implementation'] in lookup, 'unknown next implementation')
    nxt = lookup[p['next_implementation']]
    require(nxt['status'] in {'planned', 'active'}, 'next implementation is not open')
    require(all(lookup[d]['status'] == 'completed' for d in nxt['depends_on']),
            'next implementation has incomplete dependencies')
    return order


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('programme', nargs='?', type=Path,
                        default=Path(__file__).with_name('V888_BOOL_PROGRAMME.json'))
    args = parser.parse_args()
    p = load(args.programme)
    order = validate(p)
    canonical = json.dumps(p, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    print(json.dumps({'valid': True, 'milestones': len(order),
                      'sha256': hashlib.sha256(canonical.encode()).hexdigest(),
                      'next_implementation': p['next_implementation'],
                      'execution_authorized': False}, sort_keys=True))


if __name__ == '__main__':
    main()
