# P-Hacking and Multiple Comparisons: Protecting Experiment Integrity

## Definition

**P-hacking** is the practice — intentional or not — of exploiting researcher degrees of freedom to produce a statistically significant result. It includes: testing multiple metrics and reporting only the significant ones, running multiple variants and selecting the winner, checking results repeatedly until significance is reached, segmenting data until a significant subgroup is found, and switching the primary metric after observing results. Each of these practices inflates the effective false positive rate above the nominal α, producing results that appear significant but are not replicable.

**Multiple comparisons** is the specific mechanism by which testing many hypotheses simultaneously inflates the experiment-wide false positive rate. Each individual test carries a 5% false positive risk at α = 0.05. When multiple tests are run on the same dataset, these risks compound — the probability that at least one test produces a spurious significant result increases with each additional comparison.

Both are threats to experiment validity that operate silently: the individual test outputs look normal, the p-values are computed correctly, and the significance threshold appears to be respected. The inflation is in the experiment design and analysis choices, not in the arithmetic.

---

## How Multiple Comparisons Inflate the False Positive Rate

### The Mechanism

For a single hypothesis test at α = 0.05, the probability of a false positive is 5%. The probability of not producing a false positive is 95% (0.95).

For k independent tests, the probability that none produces a false positive is 0.95^k. The probability that at least one produces a false positive — the **family-wise error rate (FWER)** — is:

FWER = 1 − (1 − α)^k = 1 − 0.95^k

### The Inflation in Numbers

| Number of Tests (k) | FWER (approx.) |
|---|---|
| 1 | 5.0% |
| 2 | 9.8% |
| 5 | 22.6% |
| 10 | 40.1% |
| 20 | 64.2% |
| 50 | 92.3% |

An experiment tracking 10 metrics simultaneously — a common configuration — operates at an effective false positive rate of approximately 40%, not 5%. With 20 metrics, the probability of at least one spurious significant result exceeds 60%. At this scale, finding a significant result is nearly guaranteed even when no true effects exist.

### The Compounding Sources of Multiple Comparisons in A/B Testing

Multiple comparisons in A/B testing arise from several simultaneous sources, each of which independently inflates the FWER:

**Multiple metrics:** Testing conversion rate, revenue per user, session depth, click rate, and retention simultaneously without correction applies α = 0.05 to each, compounding the false positive risk across all five.

**Multiple variants:** An experiment with one control and three variants involves three pairwise comparisons (control vs. A, control vs. B, control vs. C), each at α = 0.05. The FWER across all three comparisons is approximately 14%, not 5%.

**Multiple segments:** Running the primary metric analysis on the full population and then re-running on mobile users, desktop users, new users, and returning users produces five comparisons. A significant subgroup result is likely even when the overall result is null.

**Multiple time windows:** Checking significance at day 3, day 7, and day 14 of an experiment is three comparisons on the same data. See the Early Stopping and Peeking document for the specific inflation this produces.

These sources compound multiplicatively. An experiment with five metrics, two variants, and three time window checks is performing up to 30 simultaneous comparisons — producing a FWER that renders individual significance claims nearly meaningless without correction.

---

## The Pre-Registration Rule

The most effective control for multiple comparisons and p-hacking is **pre-registration**: committing to the primary metric, the statistical test, the sample size, and the analysis plan before any data is collected or observed.

### What Pre-Registration Requires

Before the experiment launches, the following must be documented and locked:

- **One primary metric:** The single metric whose result will determine the Ship / Kill / Extend decision. This is the metric to which α = 0.05 applies without correction.
- **Secondary metrics:** Metrics that provide supporting evidence or monitor for harm, but whose results do not independently determine the decision. These are reported and interpreted in context, not used as alternative Ship criteria.
- **Guardrail metrics:** Metrics that must not regress. A significant regression in a guardrail is a Kill signal regardless of the primary metric result.
- **The statistical test type:** One-tailed or two-tailed, and the reasoning for the choice.
- **The planned sample size and duration:** Derived from the power calculation. Not subject to revision based on interim results.
- **Any pre-specified segment analyses:** Segment breakdowns that are planned in advance are part of the pre-registered analysis. Segment analyses run after observing results are exploratory and carry no confirmatory weight.

### Why Pre-Registration Controls P-Hacking

Pre-registration does not prevent multiple metrics from being tracked — it prevents the post-hoc selection of whichever metric happened to be significant. When the primary metric is locked before the experiment runs, the result is binary: the pre-registered metric is significant, or it is not. There is no researcher degree of freedom to select a favourable outcome after the fact.

A secondary metric that reaches significance when the primary metric does not is a hypothesis for a future experiment, not evidence that the current experiment succeeded.

### What Happens Without Pre-Registration

Without a pre-registered primary metric, the following failure mode is common and difficult to detect after the fact:

An experiment is launched tracking eight metrics. At analysis, conversion rate (the intended primary) is not significant (p = 0.11). Revenue per user is borderline (p = 0.06). Session depth is significant (p = 0.03). The team reports session depth as the primary finding and recommends shipping. The Ship decision is based on whichever metric was significant — the effective primary metric was selected after observing the data. This is p-hacking regardless of intent.

---

## The Bonferroni Correction

When multiple comparisons are unavoidable — because multiple variants, multiple metrics, or multiple pre-specified segments are all part of the confirmatory analysis — the significance threshold must be adjusted to maintain the experiment-wide FWER at α = 0.05.

The **Bonferroni correction** is the simplest and most conservative approach:

**Adjusted α = α / k**

Where k is the number of simultaneous comparisons being made.

### Application

For an experiment with one control and two variants (k = 2 pairwise comparisons):
- Adjusted α = 0.05 / 2 = **0.025**
- Each comparison must reach p < 0.025 to be declared significant

For an experiment with three pre-registered primary metrics (k = 3):
- Adjusted α = 0.05 / 3 = **0.017**
- Each metric must reach p < 0.017 to be declared significant

For an experiment with two variants and three pre-registered metrics (k = 6 comparisons):
- Adjusted α = 0.05 / 6 = **0.0083**

### Limitations of the Bonferroni Correction

The Bonferroni correction is conservative — it reduces the false positive rate below the target α when the tests are correlated, which they typically are in A/B testing (multiple metrics measured on the same users are not independent). This conservatism increases the false negative rate: real effects may fail to reach the adjusted threshold.

Alternative corrections that account for correlation between tests include:
- **Holm-Bonferroni:** A stepwise method that is uniformly more powerful than Bonferroni while controlling FWER
- **Benjamini-Hochberg:** Controls the **false discovery rate (FDR)** rather than FWER — appropriate when the goal is to limit the proportion of false positives among significant results, rather than the probability of any false positive. Preferred in exploratory contexts with many comparisons.

For A/B testing with a small number of pre-registered comparisons (k ≤ 5), Bonferroni is appropriate and simple to apply. For larger comparison sets or correlated metrics, Holm-Bonferroni or Benjamini-Hochberg should be considered.

### What the Bonferroni Correction Does Not Fix

Bonferroni corrects for pre-specified multiple comparisons. It does not correct for:

- Post-hoc metric selection (the pre-registration problem above)
- Repeated peeking at accumulating data (the early stopping problem)
- Segment analyses that were not pre-registered
- Switching the primary metric after observing results

These are design and analysis failures that correction cannot remediate. The Bonferroni correction is a planned adjustment for a planned analysis — it is not a post-hoc fix for p-hacking.

---

## Exploratory vs. Confirmatory Analysis

A clean distinction between exploratory and confirmatory analysis is the operational framework for managing multiple comparisons without eliminating useful secondary insights.

**Confirmatory analysis:** The pre-registered primary metric and any pre-registered secondary metrics or segments. Significance is evaluated at α = 0.05 (with Bonferroni correction if multiple pre-registered comparisons are present). Results from confirmatory analysis carry decision weight.

**Exploratory analysis:** All metric and segment analyses conducted after observing results, including metrics that were tracked but not pre-registered as primary. Exploratory results are reported as directional signals, not as confirmatory evidence. They generate hypotheses for future experiments. They do not constitute independent grounds for a Ship decision.

The line between the two must be drawn before the experiment launches. Any analysis conducted after observing the direction of results is exploratory by definition, regardless of the analyst's intent.

---

## Detection: Signals That P-Hacking May Have Occurred

An automated system should flag results for review when:

- No primary metric is documented in the experiment spec prior to launch
- The reported primary metric differs from the metric specified at experiment design
- The result summary reports significance in a secondary or guardrail metric but not the primary metric, and uses this as the basis for a Ship recommendation
- A large number of metrics were tracked (>5) and only one or two are significant — consistent with multiple comparisons inflation
- Significant results are reported only for specific segments (mobile, new users, one geography) with no significant aggregate result — consistent with segment p-hacking
- The reported effect is significant at p = 0.03–0.05 in an experiment with many tracked metrics and no documented Bonferroni correction

---

## Anti-Patterns

- **Tracking many metrics and reporting the significant ones:** Even without intent to deceive, selecting the significant metrics post-hoc from a large tracked set is p-hacking. All tracked metrics should be reported, and the primary metric result should be distinguished from secondary findings.
- **Running segment analyses after observing a non-significant primary result:** Searching for a significant subgroup after the aggregate result fails is the textbook definition of p-hacking. Pre-register segment analyses or treat them as exploratory.
- **Using a secondary metric as the primary when the primary fails:** The primary metric was selected for a reason. Substituting a secondary metric that happened to be significant redefines success after the fact.
- **Applying Bonferroni correction only to the metrics that failed:** Selective correction — adjusting the threshold for comparisons that were not significant while leaving the significant one unadjusted — does not control FWER.
- **Treating exploratory findings as confirmatory:** A significant finding in an exploratory analysis is a hypothesis, not a result. It requires a dedicated confirmatory experiment to validate.

---

## Summary: The Pre-Registration Checklist

The following must be locked before the experiment launches. Any item missing at analysis time is a validity flag:

| Item | Status Required at Launch |
|---|---|
| Primary metric | Defined and documented |
| Secondary metrics | Listed (not used as primary fallback) |
| Guardrail metrics | Listed with regression thresholds |
| Statistical test type | One-tailed or two-tailed, with rationale |
| Planned sample size | Derived from power calculation |
| Planned duration | Fixed — not subject to interim revision |
| Pre-specified segments | Listed (any others treated as exploratory) |
| Bonferroni correction | Applied if k > 1 confirmatory comparisons |
