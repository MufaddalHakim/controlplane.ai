# ControlPlane.ai Evaluation Report

Actual cases executed: **80**

## Detector metrics

| Detector | Precision | Recall | F1 | FPR | FNR |
|---|---:|---:|---:|---:|---:|
| privacy | 0.929 | 0.867 | 0.897 | 0.015 | 0.133 |
| hallucination | 0.526 | 1.000 | 0.690 | 0.300 | 0.000 |
| bias | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| cost | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |

## Privacy threshold tradeoff

| Threshold | Precision | Recall | FPR | Escalation rate |
|---:|---:|---:|---:|---:|
| 0.30 | 0.929 | 0.867 | 0.015 | 0.175 |
| 0.45 | 0.929 | 0.867 | 0.015 | 0.175 |
| 0.60 | 0.929 | 0.867 | 0.015 | 0.175 |
| 0.72 | 1.000 | 0.333 | 0.000 | 0.062 |
| 0.85 | 1.000 | 0.333 | 0.000 | 0.062 |

Lower thresholds catch more labeled risks but increase reviewer volume. Higher thresholds reduce review volume while increasing missed-case risk.

Latency: mean 0.381 ms, P50 0.390 ms, P95 0.654 ms.
