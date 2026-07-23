# P3 E V2 Verification Dropped-Unit Audit Verdict - 2026-07-23

Audit file:
`docs/P3_DOMAIN_DEV50_E_V2_VERIFICATION_DROPPED_AUDIT_20260723.md`

## Human Verdict

| Label | Count | Share |
| --- | ---: | ---: |
| wrong_drop | 7/13 | 54% |
| correct_drop | 5/13 | 38% |
| unclear | 1/13 | 8% |

## Interpretation

E v2 improved over E v1 but is still over-conservative.

- E v1 overkill rate: 18/20 = 90%.
- E v2 overkill rate: 7/13 = 54%.
- E v2 correct drops increased from 1 to 5, mainly filtering locations and
  organization names correctly:
  - Iraq;
  - Afghanistan;
  - Kyiv;
  - US Navy;
  - Royal Navy.
- The remaining wrong drops include 7 entities that should have been retained.

Key error pattern:

- Four wrong drops came from one row (`domain-candidate-0171`) involving
  formation/group entities such as carrier strike group, expeditionary strike
  group, and surface action group.
- Other wrong drops include valid equipment-domain basic component or carried
  weapon entities such as torpedo and lower shell part.

The verifier therefore has systematic bias against:

- military formation/group entities such as strike groups and battle groups;
- basic component or carried weapon entities such as shell parts and torpedoes.

## Decision

Verification is not worth further paid-GPU runs in the current form.

D(RAG) remains the current best domain-dev sanity result. E v1 and E v2 should
be preserved as negative/mixed verification evidence, not rerun away.

## GPU-free Follow-up

Prepare a candidate-preserving v3 verifier prompt without paid model calls:

- source text remains primary;
- RAG absence cannot justify `no` if the candidate span is found in source;
- explicit type definitions remain;
- add protection for equipment-domain formation/group entities;
- add protection for basic component, payload, and carried-weapon entities;
- keep the config unauthorized unless the human explicitly approves another
  bounded paid verifier experiment.
