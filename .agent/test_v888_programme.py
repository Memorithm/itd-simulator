"""Strategy consistency tests, not evidence of a working V888 Boolean model."""
import copy
import json
import unittest
from pathlib import Path

from validate_v888_programme import load, unique_object, validate

BASE = load(Path(__file__).with_name('V888_BOOL_PROGRAMME.json'))


class ProgrammeTests(unittest.TestCase):
    def setUp(self):
        self.p = copy.deepcopy(BASE)

    def test_current_programme(self):
        order = validate(self.p)
        self.assertEqual(len(order), 26)
        self.assertEqual(self.p['first_functional_target'], 'V888-BOOL-1.1')
        self.assertLess(order.index('V888-DATA-0'), order.index('V888-BOOL-0.1'))

    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON'):
            json.loads('{"a":1,"a":2}', object_pairs_hook=unique_object)

    def test_invalid_mutations(self):
        mutations = [
            ('unknown field', lambda p: p.update(extra=True)),
            ('schema bool', lambda p: p.update(schema_version=True)),
            ('noncanonical date', lambda p: p.update(observed_on='20260922')),
            ('wrong host', lambda p: p.update(execution_host='Debian')),
            ('wrong model', lambda p: p.update(frozen_model='ITD V30')),
            ('dataset internal', lambda p: p.update(raw_data_external=False)),
            ('holdout authority', lambda p: p['authority'].update(final_holdout_access=True)),
            ('truthy zero', lambda p: p['authority'].update(runtime_actuation=0)),
            ('other dataset', lambda p: p['source_scope'].update(materialization='v783')),
            ('invalid digest', lambda p: p['source_scope'].update(raw_synapse_sha256='bad')),
            ('bool count', lambda p: p['source_scope'].update(metadata_nodes=True)),
            ('missing family', lambda p: p['families'].pop()),
            ('duplicate stage', lambda p: p['milestones'].append(p['milestones'][0])),
            ('unknown dependency', lambda p: p['milestones'][1].update(depends_on=['missing'])),
            ('self dependency', lambda p: p['milestones'][1].update(depends_on=['ITD-30.4'])),
            ('cycle', lambda p: (p['milestones'][1].update(depends_on=['ITD-30.5']), p['milestones'][2].update(depends_on=['ITD-30.4']))),
            ('empty criteria', lambda p: p['milestones'][1].update(exit_criteria=[])),
            ('unsourced completion', lambda p: p['milestones'][1].update(status='completed')),
            ('unbound evidence', lambda p: p['milestones'][0]['evidence'][0].update(source_commit='main')),
            ('blocked next', lambda p: p['milestones'][3].update(status='blocked')),
            ('unready next', lambda p: p.update(next_implementation='V888-BOOL-1.1')),
            ('unknown target', lambda p: p.update(first_functional_target='missing')),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                candidate = copy.deepcopy(BASE)
                mutate(candidate)
                with self.assertRaises(ValueError):
                    validate(candidate)

    def test_validation_is_not_execution(self):
        before = copy.deepcopy(self.p)
        self.assertEqual(validate(self.p), validate(self.p))
        self.assertEqual(before, self.p)
        self.assertTrue(all(v is False for v in self.p['authority'].values()))

    def test_completed_prerequisite_requires_evidence(self):
        # A real URL alone is not sufficient: source commit and scope must be retained.
        self.p['milestones'][0]['evidence'][0]['scope'] = ''
        with self.assertRaisesRegex(ValueError, 'scope'):
            validate(self.p)


if __name__ == '__main__':
    unittest.main()
