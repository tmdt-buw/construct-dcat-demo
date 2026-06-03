#!/usr/bin/env python3
"""
Construct-DCAT discovery demonstration.

This script loads REAL Turtle artifacts from the repository:
  - profile/construct-dcat.ttl          (the minimal vocabulary)
  - profile/construct-dcat-shapes.ttl   (SHACL shapes)
  - catalog/example-catalog.ttl         (8 annotated datasets + IFC hierarchy)
  - tests/q_baseline.rq                 (baseline keyword query)
  - tests/q_constructdcat.rq            (Construct-DCAT typed + subclass query)

It then:
  1. Validates the catalog against the SHACL shapes (pyshacl).
  2. Runs both discovery queries against the catalog.
  3. Reports precision / recall / F1 against a declared ground truth.

Competency question (CQ):
  "Which datasets describe walls (IFC walls or their subtypes) AND commit to
   the Building Topology Ontology, regardless of lifecycle phase or format?"

Ground truth: D1, D5, D8  (declared below, see README for justification).
"""

import pathlib
import sys

from rdflib import Graph

try:
    import owlrl
    HAVE_OWLRL = True
except Exception:
    HAVE_OWLRL = False

try:
    from pyshacl import validate
    HAVE_PYSHACL = True
except Exception:
    HAVE_PYSHACL = False

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "example-catalog.ttl"
PROFILE = ROOT / "profile" / "construct-dcat.ttl"
SHAPES = ROOT / "profile" / "construct-dcat-shapes.ttl"
Q_BASE = ROOT / "tests" / "q_baseline.rq"
Q_CX = ROOT / "tests" / "q_constructdcat.rq"

# Ground truth for the competency question (see README for per-dataset rationale).
GROUND_TRUTH = {"D1", "D5", "D8"}


def short(uri: str) -> str:
    # take the part after the last # or /, handling the ex:cat# namespace
    return uri.split("#")[-1].split("/")[-1]


def run_query(graph: Graph, query_path: pathlib.Path):
    q = query_path.read_text()
    return {short(str(row[0])) for row in graph.query(q)}


def prf(retrieved, truth):
    tp = len(retrieved & truth)
    p = tp / len(retrieved) if retrieved else 0.0
    r = tp / len(truth) if truth else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def main():
    # ---- load catalog (+ profile, so subclass/range terms are available) ----
    g = Graph()
    g.parse(PROFILE, format="turtle")
    g.parse(CATALOG, format="turtle")

    # Apply RDFS inference so that cx:BIMDataset / cx:AASDataset instances are
    # entailed to be dcat:Dataset instances (rdfs:subClassOf), and the discovery
    # queries behave as they would over an RDFS-aware triplestore. Without this,
    # "?d a dcat:Dataset" would not match a subclass instance.
    if HAVE_OWLRL:
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
        inf = "RDFS inference applied (owlrl)"
    else:
        inf = "owlrl not installed; queries assume explicit typing only"
    print(f"Loaded catalog: {CATALOG.name}  ({len(g)} triples; {inf})\n")

    # ---- 1. SHACL validation ----
    print("=" * 60)
    print("1. SHACL VALIDATION (profile/construct-dcat-shapes.ttl)")
    print("=" * 60)
    if HAVE_PYSHACL:
        data_g = Graph()
        data_g.parse(CATALOG, format="turtle")
        shapes_g = Graph()
        shapes_g.parse(SHAPES, format="turtle")
        conforms, _report_graph, report_text = validate(
            data_g,
            shacl_graph=shapes_g,
            inference="rdfs",
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
        )
        print(f"Conforms (violations only): {conforms}")
        # Show warnings/violations summary lines
        for line in report_text.splitlines():
            s = line.strip()
            if s.startswith(("Constraint Violation", "Severity", "Message",
                             "Focus Node")):
                print("  " + s)
        print()
    else:
        print("pyshacl not installed; skipping (pip install pyshacl)\n")

    # ---- 2 + 3. discovery queries + metrics ----
    print("=" * 60)
    print("2. DISCOVERY: competency question")
    print("=" * 60)
    print('CQ: walls (IFC walls or subtypes) AND committing to BOT.')
    print(f"Ground truth: {sorted(GROUND_TRUTH)}\n")

    base = run_query(g, Q_BASE)
    cx = run_query(g, Q_CX)

    pb, rb, fb = prf(base, GROUND_TRUTH)
    pc, rc, fc = prf(cx, GROUND_TRUTH)

    print("Baseline DCAT (keyword match on 'wall'):")
    print(f"  retrieved : {sorted(base)}")
    print(f"  P={pb:.2f}  R={rb:.2f}  F1={fb:.2f}")
    fp_b = sorted(base - GROUND_TRUTH)
    fn_b = sorted(GROUND_TRUTH - base)
    print(f"  false positives: {fp_b}   missed: {fn_b}\n")

    print("Construct-DCAT (typed asset + rdfs:subClassOf* over IFC + BOT):")
    print(f"  retrieved : {sorted(cx)}")
    print(f"  P={pc:.2f}  R={rc:.2f}  F1={fc:.2f}")
    fp_c = sorted(cx - GROUND_TRUTH)
    fn_c = sorted(GROUND_TRUTH - cx)
    print(f"  false positives: {fp_c}   missed: {fn_c}\n")

    print("=" * 60)
    print("3. SUMMARY")
    print("=" * 60)
    print(f"  {'method':<22}{'P':>6}{'R':>6}{'F1':>6}")
    print(f"  {'baseline DCAT':<22}{pb:>6.2f}{rb:>6.2f}{fb:>6.2f}")
    print(f"  {'Construct-DCAT':<22}{pc:>6.2f}{rc:>6.2f}{fc:>6.2f}")

    # ---- write a small results file ----
    out = ROOT / "results" / "results.md"
    out.write_text(
        "# Discovery results\n\n"
        "Competency question: walls (IFC walls or subtypes) AND committing to BOT.\n\n"
        f"Ground truth: {sorted(GROUND_TRUTH)}\n\n"
        "| Method | Precision | Recall | F1 |\n"
        "|---|---|---|---|\n"
        f"| Baseline DCAT (keyword) | {pb:.2f} | {rb:.2f} | {fb:.2f} |\n"
        f"| Construct-DCAT (typed + subclass) | {pc:.2f} | {rc:.2f} | {fc:.2f} |\n\n"
        f"- Baseline retrieved {sorted(base)} "
        f"(false positives {fp_b}, missed {fn_b}).\n"
        f"- Construct-DCAT retrieved {sorted(cx)} "
        f"(false positives {fp_c}, missed {fn_c}).\n\n"
        "_Illustrative worked example on a small constructed catalog; "
        "not a real-world retrieval benchmark._\n"
    )
    print(f"\nWrote {out.relative_to(ROOT)}")

    # exit non-zero if the demo's own expectation breaks (keeps it a real test)
    assert cx == GROUND_TRUTH, "Construct-DCAT query did not return the expected set"
    assert base != GROUND_TRUTH, "Baseline unexpectedly matched ground truth"


if __name__ == "__main__":
    main()
