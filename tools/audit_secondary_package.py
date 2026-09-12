"""Compare avatar-authored PhysBone values with exported manifest; never copy raw assets into Git."""
import json
import math
import re
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'unity/TanakaCap/Assets/HAOLAN/Phys_Haolan.prefab'
text = source.read_text(encoding='utf-8')
docs = dict(re.findall(r'--- !u!\d+ &(-?\d+)\n(.*?)(?=\n--- !u!|\Z)', text, re.S))
with zipfile.ZipFile(root / 'builds/lab/avatars/haolan.tcap') as archive:
    physics = json.loads(archive.read('manifest.json'))['secondaryPhysics']
checked = 0
for chain in physics['chains']:
    raw = docs[chain['sourceId']]
    for key in ('pull', 'spring', 'stiffness', 'gravity', 'gravityFalloff', 'immobile', 'radius', 'maxAngleX', 'maxAngleZ', 'integrationType', 'immobileType', 'limitType', 'multiChildType'):
        found = re.search(r'^  ' + key + r': ([^\n]+)', raw, re.M)
        assert found and math.isclose(float(found[1]), chain[key], rel_tol=1e-6, abs_tol=1e-6), (chain['root'], key)
        checked += 1
    expected_refs = re.search(r'^  colliders:\n((?:  -[^\n]*\n)*)', raw, re.M)
    expected_ids = set(re.findall(r'fileID: (-?\d+)', expected_refs[1])) - {'0'} if expected_refs else set()
    assert {physics['colliders'][i]['sourceId'] for i in chain['colliders']} == expected_ids
    for key, curve in chain.items():
        if not key.endswith('Curve'): continue
        block = re.search(r'^  ' + key + r':\n(.*?)(?=^  [A-Za-z_]|\Z)', raw, re.M | re.S)
        values = re.findall(r'^      value: ([^\n]+)', block[1], re.M) if block else []
        assert len(values) == len(curve['keys']), (chain['root'], key)
        for expected, actual in zip(values, curve['keys']):
            assert math.isclose(float(expected), actual['value'], rel_tol=1e-6, abs_tol=1e-6)
for collider in physics['colliders']:
    raw = docs[collider['sourceId']]
    for key in ('radius', 'height', 'shapeType', 'insideBounds', 'bonesAsSpheres'):
        expected = float(re.search(r'^  ' + key + r': ([^\n]+)', raw, re.M)[1])
        assert math.isclose(expected, collider[key], rel_tol=1e-6, abs_tol=1e-6)
        checked += 1
report = dict(status='passed', chains=len(physics['chains']), bones=len(physics['bones']), colliders=len(physics['colliders']), scalar_checks=checked, curves_and_collider_references=True)
output = root / 'results/secondary-motion/source-audit.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
