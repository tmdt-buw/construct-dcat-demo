# Discovery results

Competency question: walls (IFC walls or subtypes) AND committing to BOT.

Ground truth: ['D1', 'D5', 'D8']

| Method | Precision | Recall | F1 |
|---|---|---|---|
| Baseline DCAT (keyword) | 0.33 | 0.33 | 0.33 |
| Construct-DCAT (typed + subclass) | 1.00 | 1.00 | 1.00 |

- Baseline retrieved ['D1', 'D2', 'D3'] (false positives ['D2', 'D3'], missed ['D5', 'D8']).
- Construct-DCAT retrieved ['D1', 'D5', 'D8'] (false positives [], missed []).

_Illustrative worked example on a small constructed catalog; not a real-world retrieval benchmark._
