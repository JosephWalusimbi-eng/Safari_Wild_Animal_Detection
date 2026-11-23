# v1 vs v2 (small model, 3 seeds each)

Mean ± population std over seeds. UWEC = 47 team phone photos (never trained on).

| Metric | v1 | v2 |
|---|---|---|
| test top-1 (n=559) | 0.909 ± 0.007 | 0.924 ± 0.006 |
| UWEC top-1, all (n=47) | 0.191 ± 0.030 | 0.170 ± 0.046 |
| UWEC top-1, regular classes (n=24: bird 8, chimp 7, tiger 3, zebra 5, croc 1) | 0.306 ± 0.020 | 0.208 ± 0.090 |
| UWEC top-1, low-data classes (n=23: lion 9, buffalo 9, cheetah 5) | 0.072 ± 0.054 | 0.130 ± 0.000 |

## UWEC correct per class, per seed (v1 | v2)

| class | n | v1 seeds 0/1/2 | v2 seeds 0/1/2 |
|---|---|---|---|
| bird | 8 | 0/0/0 | 0/0/0 |
| buffalo | 9 | 0/0/0 | 0/0/0 |
| cheetah | 5 | 0/0/2 | 3/3/3 |
| chimpanzee | 7 | 0/0/0 | 0/0/0 |
| crocodile | 1 | 0/1/0 | 0/0/0 |
| lion | 9 | 3/0/0 | 0/0/0 |
| tiger | 3 | 2/2/3 | 2/2/0 |
| zebra | 5 | 5/4/5 | 4/5/2 |

## Paired UWEC changes, seed s of v1 vs seed s of v2 (summed over 3 seeds, 141 image-seeds)

wrong->right: 8   right->wrong: 11   (net -3)

## Validation (selection metric) and training length

| run | best val top-1 | epoch of best | epochs run |
|---|---|---|---|
| v1_n_seed0 | 0.901 | 10 | 33 |
| v1_n_seed1 | 0.899 | 31 | 39 |
| v1_n_seed2 | 0.910 | 22 | 44 |
| v2_n_seed0 | 0.908 | 26 | 41 |
| v2_n_seed1 | 0.897 | 14 | 47 |
| v2_n_seed2 | 0.890 | 26 | 27 |
