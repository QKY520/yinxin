# Experiment Configurations

Store one YAML file per run. Every configuration must include the dataset,
model, prompt version, shot count, example-selection mode, enhancement flags,
seed, and output paths.

`p1_public_data.yaml` is the pinned public-data preparation configuration. It
records source revisions, licenses, input hashes, remote paths, support K values,
and the sampling seed used by the P1 pipeline.

`p2_schema_draft.yaml` records the human-approved Pause A schema and approval
provenance. `p2_distant_supervision.yaml` pins the GPU-free exact-match proposal
run, including immutable input hashes, output paths, and guards that prohibit
LLM use, human annotation, splitting, and freezing.
