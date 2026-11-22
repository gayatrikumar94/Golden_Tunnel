# Golden Tunnel: Learning Guide (no coding background needed)

This guide explains the project twice: first the **bioprocess science** (why anyone needs a golden tunnel), then the **code** (how a computer builds one). Read it top to bottom once; later use it as a reference.

---

## Part 1 - The bioprocess concepts

### 1.1 What is being made, and where?
Many modern medicines (monoclonal antibodies, "mAbs") are proteins made by living cells. The workhorse cell is the **CHO cell** (Chinese Hamster Ovary). The cells grow in a stainless-steel or single-use plastic tank called a **bioreactor**, bathed in a nutrient liquid (**media**). The cells secrete the antibody into the liquid. Later, **downstream** steps purify it.

A **fed-batch** run is the most common mode: start with media and cells, then add concentrated nutrients ("feeds") on a schedule over about 14 days, and harvest at the end. Each run is called a **batch** (or lot).

### 1.2 Why monitor batches at all?
A 14-day run in a large bioreactor can be worth hundreds of thousands to millions of dollars. If something drifts on day 4 and nobody notices until day 14, the whole batch is wasted (or fails quality release). Regulators (FDA, EMA) also expect manufacturers to show their process stays in a **state of control**. This is called **Continuous Process Verification (CPV)**, which is on your resume from Dr. Reddy's.

### 1.3 The vocabulary you must know

| Term | Plain meaning | In this project |
|---|---|---|
| **Titer** | Concentration of the final product (g/L). The headline "how well did the batch do" number. | `titer_g_L` |
| **CPP** (Critical Process Parameter) | A knob or condition that, if it drifts, can hurt product quality. | pH, DO |
| **CQA** (Critical Quality Attribute) | A property of the product that must stay in range (e.g., purity, glycosylation). | Not simulated (see Next Steps) |
| **IPC** (In-Process Control) | A check during manufacturing with a pass/fail range. | The tunnel acts like one |
| **pH** | Acidity. CHO cells like ~6.9-7.1. Cells make lactic acid, so pH falls unless base/CO2 is controlled. | `pH` |
| **DO** (Dissolved Oxygen) | How much oxygen is dissolved in the liquid, as % of air-saturated. Controller holds it near a setpoint (~40%) by adding oxygen/air. | `DO` |
| **OUR** (Oxygen Uptake Rate) | How fast the cells consume oxygen. More healthy, active cells = higher OUR. Rises, peaks, then falls as cells age. | `OUR` |
| **Deviation** | A documented event where something didn't go to plan. Needs investigation and CAPA. | `deviation_recorded` |
| **QbD / DOE** | Quality by Design / Design of Experiments: learning how parameters affect quality, so ranges are justified by data. | Where you would justify `k` |

### 1.4 What is a "golden batch"?
Among all your historical batches, some were *ideal*: good titer, good quality, no deviations. Those are **golden batches**. They represent "this is what a healthy run looks like."

Important: golden is a **quality decision**, not only a statistics one. In this project the rule is: top 50% by titer **and** no recorded deviation. A real plant would also require passing quality release and a clean batch record.

### 1.5 What is the "golden tunnel"?
Imagine plotting pH versus time for every golden batch. You get a bundle of curves that look alike but not identical. Now at every time point (day 0, day 0.25, day 0.5 ...) compute:

- the **average** value across golden batches, and
- the **standard deviation (SD)**, which measures how spread out they are.

Draw a band from `average - k x SD` to `average + k x SD`. This band is the **golden tunnel** (also called a golden batch envelope, control corridor, or batch trajectory limits). A new batch that stays inside is behaving like your best batches. A batch that leaves the tunnel is a candidate for investigation *while the batch is still running*, which is the whole point.

### 1.6 Choosing `k` (how wide the tunnel is)
`k` is a trade-off, and it is the single most important setting:

| k | Tunnel | Result |
|---|---|---|
| 1 | Narrow | Catches everything, but also raises many **false alarms** (healthy batches look suspicious). Operators stop trusting it. |
| 2 | Medium | Common for early warning ("alert" limit). |
| 3 | Wide | Few false alarms; only clear problems alarm. Common for "action" limits. |

When we tested this project on simulated data (more detail in the README), k=1 alarmed on **100%** of healthy batches, k=2 on about 29%, and k=3 on about 8%. Meanwhile all the faulty batches alarmed at every setting. This is exactly the statistics lesson of *sensitivity vs. false-alarm rate*. In real work you choose `k` using DOE/characterization data and agree it with Quality.

Your resume mentions ±1 SD bands for a quick comparison picture. That is a fine *visual*. For *alarming*, wider limits or a consecutive-readings rule (below) are usually used.

### 1.7 The "consecutive readings" rule
Sensors are noisy. One strange reading is often just noise. So the monitor only raises an alarm when **3 readings in a row** (default, 0.75 day) are outside the tunnel. This is borrowed from classical **SPC (Statistical Process Control)** run rules. Lower it for faster alarms; raise it for fewer false alarms.

### 1.8 What this simple method does NOT do (be honest in interviews)
- It looks at each parameter **separately** (univariate). Industry also uses **multivariate** methods (PCA/PLS "batch evolution models" in SIMCA) that notice when parameters move *together* in an unusual way even if each looks fine alone. Your M.S. and resume show you know MVDA, so you can say: "the tunnel is the simple first line; MVDA is the next layer."
- It assumes all batches are **time-aligned** (same clock, same sampling). Real batches have different phases and lengths; you'd align them first (by phase or with Dynamic Time Warping).
- Data here is **simulated**. The *method* is real; the numbers are not measurements.
- The tunnel is only as good as the golden batches. Too few (<10-15), or ones that are secretly unusual, give a misleading tunnel.

---

## Part 2 - The coding concepts, from zero

### 2.1 What is Python, and what is a "library"?
Python is a programming language: you write instructions in a text file (`.py`), and Python carries them out. A **library** is a toolbox someone else wrote so you don't start from scratch. We use three:

- **NumPy**: fast math on lists of numbers (arrays).
- **pandas**: spreadsheets in code. Its main object is a **DataFrame**, a table with named columns, like an Excel sheet.
- **matplotlib**: draws charts.

### 2.2 Building blocks you will see
- **Variable**: a named box holding a value. `k = 3` means "k is 3".
- **Function**: a reusable recipe. `def build_tunnel(...)` defines one; calling `build_tunnel(...)` runs it and may `return` an answer.
- **List**: ordered items, e.g. `["pH", "DO", "OUR"]`.
- **Dictionary (dict)**: labelled items, e.g. `{"pH": 0.02, "DO": 1.0}` where you look up by label.
- **Loop**: repeat something. `for p in parameters:` means "do this once for pH, once for DO, once for OUR".
- **if / else**: make a decision.
- **Class / dataclass**: a custom container that bundles related data. Our `Tunnel` bundles the table, the `k`, and which batches built it.
- **Module / package**: a `.py` file / a folder of them. `from golden_tunnel import build_tunnel` means "bring that function in".
- **Comments** (`# text`) and **docstrings** (`"""text"""`) are notes for humans; Python ignores them.

### 2.3 How the project is organised

```
golden-tunnel/
  run_demo.py            <- the "start button": runs everything in order
  golden_tunnel/         <- the package (the real logic)
    simulate.py          <- Step 1: fake-but-realistic batch data
    tunnel.py            <- Step 2: pick golden batches, build the tunnel
    monitor.py           <- Step 3: check a batch against the tunnel
    plotting.py          <- Step 4: charts
  tests/                 <- automatic checks that the code behaves
  data/ reports/ figures/<- outputs the demo creates
  docs/                  <- this guide
  requirements.txt       <- list of libraries to install
```

### 2.4 The data shape (the most important idea)
Time-series data is stored in **long format**: one row per batch per time point.

| batch_id | time_day | pH | DO | OUR |
|---|---|---|---|---|
| B001 | 0.00 | 7.00 | 40.1 | 0.00 |
| B001 | 0.25 | 6.99 | 39.8 | 0.08 |
| ... | ... | ... | ... | ... |
| B002 | 0.00 | 7.01 | 40.3 | 0.00 |

A second small table, the **summary**, has one row per batch: `batch_id, titer_g_L, deviation_recorded, low_titer`.

### 2.5 Walking through the code, step by step

**Step 1 - `simulate.py`.** For each batch it draws random "personality" numbers (when cells peak, how high OUR gets), builds smooth curves for OUR, DO and pH, adds sensor noise, and for ~30% of batches injects a problem (a pH drift, a DO dip, or slow growth). Titer is computed from the area under the OUR curve (cumulative oxygen use ~ cumulative cell activity), reduced when a fault happened. The `fault_type` column is the *answer key*, used only to grade the monitor later; the tunnel never sees it.

**Step 2 - `tunnel.py`.**
1. `select_golden_batches` keeps batches in the top half by titer with no recorded deviation.
2. `build_tunnel` takes those batches, and for each parameter uses `pivot` to reshape the long table into a grid (rows = batches, columns = time points). Then it takes the column average (`mean`) and column SD (`std`). `lower = mean - k*sd`, `upper = mean + k*sd`.
3. Two safety touches: a **smoothing** step (3-point rolling average) so edges aren't jagged, and a **minimum SD floor** so the tunnel is never paper-thin where batches happen to agree (e.g. at day 0).

**Step 3 - `monitor.py`.** For a new batch and each parameter:
1. Line up the tunnel with the batch's time stamps (`np.interp`).
2. Mark each reading as inside or outside.
3. Compute a **z-score**: `(value - average) / SD`, "how many SDs from normal".
4. Raise an alarm at the first moment 3 consecutive readings are outside.
5. Report % of readings inside, the alarm day, and which parameter alarmed.

`summarize_performance` then compares alarms with what really happened (low titer or not) and counts four outcomes: **true positive** (alarm, and it was bad), **false positive** (false alarm), **false negative** (missed), **true negative** (quiet and fine). From these: **precision** (when it alarms, how often is it right) and **recall** (of the bad batches, how many did it catch).

**Step 4 - `run_demo.py`.** Orchestrates: simulate, split into 70% "history" and 30% "new batches", build tunnel from history only, monitor the new ones, print results, save charts.

### 2.6 Why the 70/30 split matters
If you built the tunnel from all batches and then tested on those same batches, you'd be grading your own homework. The tunnel would look better than it really is. Keeping new batches separate mimics real life: the tunnel is built from the past and used on future batches. (Same idea as train/test split in machine learning.)

### 2.7 A bug worth knowing about (a real lesson from building this)
During development the first results looked bad (healthy batches alarming constantly). The cause was one line that shuffled batch IDs *in place* and silently scrambled the labels of the summary table, so batch B013 was labelled "healthy" but had the data of a faulty one. The fix was to shuffle a **copy** (`rng.permutation`). The lesson, valuable in any data job: **when results look wrong, suspect your data handling before your model**, and always sanity-check by plotting a specific example. That is also a great interview story.

### 2.8 Tests
`tests/test_golden_tunnel.py` contains small automatic checks, e.g. "the lower limit is always below the mean", "a batch with an artificial pH crash does alarm", "one noisy reading does *not* alarm". Run them with `pytest`. In regulated industries, "show me it works and keeps working" is a core habit (validation).

### 2.9 Git and GitHub (30-second version)
**Git** records snapshots (commits) of your project so you can go back and see what changed. **GitHub** is a website that hosts Git projects so others (recruiters!) can see them. See `PUBLISH_TO_GITHUB.md`.

---

## Part 3 - Run it and experiment

```bash
python run_demo.py                    # default
python run_demo.py --k 2              # tighter tunnel -> more alarms, more false alarms
python run_demo.py --consecutive 5    # needs 5 bad readings in a row -> fewer false alarms, later alarms
python run_demo.py --seed 7           # different random batches
```
Open `figures/` after each run. Try to predict how the numbers change *before* you run; that is how intuition forms.

## Part 4 - Ideas to extend it (pick one for v2)
1. **Real-world realism**: add phases (growth / production), batches of different lengths, and Dynamic Time Warping to align them.
2. **Multivariate tunnel**: replace per-parameter bands with a PCA/PLS batch-evolution model (Hotelling's T2 and DModX), the SIMCA approach.
3. **Alert vs. action limits**: two tunnels (k=2 and k=3) with different responses.
4. **Dashboard**: Streamlit app where you upload a batch CSV and see the tunnel, status, and z-scores live.
5. **Add CQAs and more variables**: viable cell density, glucose, lactate, osmolality.
6. **Choose k from data**: scan k and plot a false-alarm vs. detection curve (ROC-style).

## Part 5 - How to talk about it (resume / interview)
> "I built a golden-tunnel batch monitor in Python. It selects golden batches by titer and deviation history, builds mean ± k·SD trajectory limits for pH, DO and OUR, and flags new batches using a consecutive-excursion rule. On simulated CHO fed-batch data with a 70/30 history/new split, k=3 flagged every faulty batch with an ~8% false-alarm rate on healthy ones, and I characterised the trade-off across k. I also found and fixed a label-leakage bug during validation. Next I'd add multivariate batch-evolution modelling and time alignment."

Only state numbers from a run you did yourself, and say they're from simulated data.

## Glossary
**Bioreactor**: tank where cells grow. **Fed-batch**: nutrients added during the run. **Titer**: product concentration. **CPP/CQA**: critical process parameter / quality attribute. **CPV**: continuous process verification. **SPC**: statistical process control. **SD**: standard deviation. **z-score**: distance from average in SDs. **MVDA**: multivariate data analysis. **PAT**: process analytical technology. **Precision / Recall**: correctness of alarms / share of real problems caught. **Long format**: one row per observation. **DataFrame**: pandas table.
