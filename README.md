# Construct-DCAT — discovery demo

A small, self-contained demonstration that a **Construct-DCAT** profile improves
*domain-aware discoverability* of construction datasets compared with baseline
DCAT/DCAT-AP keyword search.

This repository accompanies the poster *"Construct-DCAT: A Requirements-Driven DCAT
Extension for Domain-Aware Discovery in Construction Dataspaces"* (SEMANTiCS 2026,
Posters & Demos).

## What this is (and is not)

- The profile in [`profile/`](profile/) is a **minimal worked example** produced via the
  requirements-driven workflow of our visual profile editor
  ([tmdt-buw/visual-profile-editor](https://github.com/tmdt-buw/visual-profile-editor)).
  Producing a profile in the editor requires **expert requirements input**; the example
  here reflects one such minimal extension.
- It is **conformant in principle**, not a full DCAT-AP profile: every `cx:*Dataset` is
  an `rdfs:subClassOf dcat:Dataset`, and the anchoring properties have `dcat:Dataset` in
  their domain, so any annotated record remains a valid `dcat:Dataset`. We do **not**
  claim DCAT-AP mandatory/recommended cardinalities, controlled-vocabulary obligations,
  or a formal conformance statement — those are future work.
- The catalog and metrics are an **illustrative example on a small constructed catalog**,
  built to expose specific failure modes of keyword search. The perfect Construct-DCAT
  score is a property of this constructed example, **not** a real-world retrieval
  benchmark. A large-scale evaluation on operational catalogs is future work.

## Repository layout

```
profile/
  construct-dcat.ttl          # the minimal vocabulary: 2 subclasses + 4 anchoring properties
  construct-dcat-shapes.ttl   # SHACL shapes ("conform in principle")
catalog/
  example-catalog.ttl         # 8 datasets annotated with the profile + IFC hierarchy slice
tests/
  q_baseline.rq               # baseline DCAT keyword query
  q_constructdcat.rq          # Construct-DCAT typed + subclass-aware query
  run_discovery_demo.py       # loads the files, validates with SHACL, runs both queries
results/
  results.md                  # generated metrics table
```

## Quick start

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tests/run_discovery_demo.py
```

The script writes the regenerated table to [`results/results.md`](results/results.md).
The expected outcome is:

- baseline DCAT keyword search returns `D1, D2, D3`;
- Construct-DCAT typed/subclass-aware search returns `D1, D5, D8`;
- Construct-DCAT therefore reaches precision, recall, and F1 of `1.00` on this small
  constructed example.

The SHACL validation step may report a warning for intentionally weakly annotated
records. Warnings are part of the demonstration: they show guidance for better semantic
anchoring without blocking the discovery comparison.

## The competency question

> **CQ:** Which datasets describe walls (IFC walls or their subtypes) **and** commit to
> the Building Topology Ontology (BOT), regardless of lifecycle phase or file format?

**Ground truth: `D1`, `D5`, `D8`.** Rationale per dataset:

| id | describes | uses BOT | in answer? | why |
|----|-----------|:--------:|:----------:|-----|
| D1 | `ifc:IfcWall` | yes | ✅ | a wall, commits to BOT |
| D2 | (wall *schedule*) | yes | ❌ | a schedule, not a wall description |
| D3 | `ifc:IfcSensor` | no | ❌ | wall-*mounted* sensor, not a wall |
| D4 | `ifc:IfcDoor` | yes | ❌ | doors, not walls |
| D5 | `ifc:IfcWallStandardCase` | yes | ✅ | IFC wall **subtype**; keyword says "partition elements" |
| D6 | (topology) | yes | ❌ | uses BOT but not about walls |
| D7 | — | no | ❌ | unrelated (HVAC) |
| D8 | `ifc:IfcWallElementedCase` | yes | ✅ | IFC wall **subtype**; keyword says "facade buildup" |

## How discovery differs

**Baseline DCAT/DCAT-AP** can only match free-text `dcat:keyword`:

```sparql
SELECT ?d WHERE {
  ?d a dcat:Dataset ; dcat:keyword ?k .
  FILTER(CONTAINS(LCASE(STR(?k)), "wall"))
}
```

This matches one true wall (D1) but wrongly returns D2 (a wall *schedule*) and D3 (a
wall-*mounted* sensor), and **misses D5 and D8** — real IFC wall subtypes whose keywords
never contain the string "wall".

**Construct-DCAT** uses typed links and subclass reasoning over the IFC hierarchy:

```sparql
SELECT ?d WHERE {
  ?d a dcat:Dataset ;
     cx:describesAssetType ?cls ;
     cx:usesOntology bot: .
  ?cls rdfs:subClassOf* ifc:IfcWall .
}
```

This returns exactly `D1, D5, D8`.

## Results

| Method | Precision | Recall | F1 |
|---|---|---|---|
| Baseline DCAT (keyword) | 0.33 | 0.33 | 0.33 |
| Construct-DCAT (typed + subclass) | 1.00 | 1.00 | 1.00 |

(Regenerate with the script below; see [`results/results.md`](results/results.md).)

## Reproduce the results

```bash
pip install -r requirements.txt
python tests/run_discovery_demo.py
```

The script (1) validates the catalog against the SHACL shapes, (2) runs both queries,
and (3) prints and writes the precision/recall/F1 table. RDFS inference is applied so
that `cx:BIMDataset`/`cx:AASDataset` instances are entailed to be `dcat:Dataset`
instances, as they would be over an RDFS-aware triplestore.

## Demo scope

This repository is intentionally narrow. It demonstrates one competency question over a
small catalog with known ground truth. It is useful for showing the discoverability gain
from typed semantic anchors, but it should not be read as a benchmark of real-world
catalog performance or as a complete DCAT-AP conformance package.

## Replacing the example with real editor output

To use a profile you actually exported from the visual profile editor, drop your
`construct-dcat.ttl` and `construct-dcat-shapes.ttl` into [`profile/`](profile/),
re-annotate (or extend) [`catalog/example-catalog.ttl`](catalog/example-catalog.ttl),
and re-run the script. The queries in [`tests/`](tests/) are plain `.rq` files you can
adapt to your competency questions.

## License

Code: MIT. Profile and example data: CC BY 4.0.
