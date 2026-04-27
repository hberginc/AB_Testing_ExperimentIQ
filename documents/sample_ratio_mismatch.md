# Sample Ratio Mismatch (SRM): Detection, Impact, and Response

## Definition

A **Sample Ratio Mismatch (SRM)** occurs when the observed ratio of users assigned to each experiment variant differs meaningfully from the intended assignment ratio. It is a signal that the randomisation or traffic assignment mechanism has failed — that users are not being allocated to variants as designed.

SRM is an experiment validity issue, not a statistical outcome issue. A result produced by an experiment with an SRM cannot be trusted regardless of its statistical significance, effect size, or direction. SRM detection must occur before any metric analysis is interpreted or acted upon.

---

## Why SRM Matters

Experiment analysis assumes that assignment to control and variant is random and that the observed ratio of users in each group reflects the intended split. When this assumption is violated:

- The two groups are no longer comparable — systematic differences in who ends up in each variant may confound the measured effect
- Any observed lift or regression may be an artefact of the assignment bias rather than the treatment
- p-values, confidence intervals, and effect size estimates are all invalidated — they are computed under the assumption of valid randomisation

An SRM does not indicate which direction the bias runs or how large the confounding effect is. It indicates that the experiment cannot be used to draw causal conclusions in its current state.

---

## How to Detect SRM: Chi-Square Test on Traffic Split

SRM is detected by testing whether the observed user counts per variant are consistent with the intended assignment ratio, using a **chi-square goodness-of-fit test**.

### The Test

Given:
- **N_total:** Total users assigned across all variants
- **Intended split:** The pre-specified allocation ratio (e.g., 50/50, 33/33/33)
- **Expected count per variant:** N_total × intended proportion
- **Observed count per variant:** Actual users assigned

The chi-square statistic is:

χ² = Σ [ (Observed − Expected)² / Expected ]

Summed across all variants. The resulting statistic is compared against a chi-square distribution with (number of variants − 1) degrees of freedom.

### Threshold

Flag as SRM when **p < 0.01** on the chi-square test. A stricter threshold than the standard 0.05 is appropriate here because:
- The cost of a false negative (missing a real SRM) is high — it means acting on invalid results
- Traffic split checks are low-noise by design; genuine mismatches tend to produce very small p-values
- A p-value between 0.01 and 0.05 on the SRM check warrants investigation even if not a hard flag

### Example

Intended split: 50% control, 50% variant. Total users: 100,000.

| Variant | Expected | Observed | (O−E)²/E |
|---|---|---|---|
| Control | 50,000 | 50,847 | 14.4 |
| Variant | 50,000 | 49,153 | 14.4 |

χ² = 28.8, df = 1, p < 0.0001 → **SRM confirmed.**

A discrepancy of ~850 users on 100,000 total (~0.85%) is sufficient to produce a highly significant SRM. SRM does not require a large absolute discrepancy — it requires a discrepancy that is unlikely to have arisen by chance.

---

## Common Causes of SRM

Understanding the likely cause is necessary for deciding whether and how the experiment can be salvaged.

**Triggering and logging asymmetry:**
The most common cause. Users are assigned to a variant but the assignment event is not logged symmetrically across variants — for example, if the variant introduces a redirect that causes some assignment events to be dropped. The variant group appears smaller than intended because some assigned users are never recorded.

**Bot and non-human traffic filtering:**
If bot filtering is applied after assignment but the filter disproportionately removes users from one variant (e.g., because the variant page loads slower and bots time out more frequently), the observed ratio will be skewed.

**Caching and CDN effects:**
If the variant changes a cached resource, users hitting the cache may not receive the treatment and may be excluded from logging. Control users are unaffected. This produces a systematic undercount in the variant.

**Experiment start-up effects:**
A ramp-up period where traffic is gradually increased can produce SRM if the ramp disproportionately affects one variant. Experiments should be analysed from a stable traffic allocation, not from the moment traffic first flows.

**Client-side rendering failures:**
If the variant involves a client-side change that fails to render for a subset of users, those users may complete the assignment step but not receive the treatment — and may or may not be counted depending on where in the funnel logging occurs.

**Incorrect experiment configuration:**
The intended split was set incorrectly in the experimentation platform, or was changed mid-experiment. Always verify the configured split against the expected split at experiment start.

---

## What SRM Invalidates

When SRM is confirmed, the following outputs of the experiment are unreliable and should not be used for decision-making:

- **All metric estimates:** Effect sizes, relative lifts, and absolute differences between variants
- **All p-values and significance conclusions:** Computed under the assumption of valid randomisation
- **All confidence intervals:** The interval bounds do not reflect the true uncertainty given the assignment bias
- **Segment-level analyses:** Breakdowns by device, geography, or user type are equally invalidated — the bias may be unevenly distributed across segments

**What SRM does not invalidate:**
- The experiment hypothesis and design — these can be re-run once the root cause is resolved
- Qualitative observations made during the experiment period — useful for diagnosing the cause
- The pre-experiment power calculation — sample size requirements remain valid for a re-run

---

## What to Do When SRM Is Detected

SRM resolution follows a structured sequence. Do not skip to re-running the experiment before diagnosing the cause — an unresolved root cause will produce SRM again.

**Step 1: Confirm the mismatch is not a reporting artefact**
Verify that the user counts are being pulled from the correct data source and that the query logic is not inadvertently filtering one variant. A miscounted denominator is more common than a true assignment failure and is faster to resolve.

**Step 2: Identify the likely cause**
Review the common causes above against the experiment configuration. Check: logging symmetry, bot filtering logic, caching behaviour, ramp-up timeline, and platform configuration. The cause should be identified before any remediation is attempted.

**Step 3: Do not attempt to correct for SRM statistically**
Reweighting, matching, or subsetting the data to restore the intended ratio does not recover a valid experiment — it introduces new selection biases and does not restore the causal validity that randomisation provides. The result of a corrected SRM experiment is still not trustworthy.

**Step 4: Assess salvageability**
In limited cases, SRM can be partially addressed:
- If the mismatch is caused by a logging issue that has since been fixed, the experiment may be re-analysed from the point the logging was corrected — provided the pre-correction period is excluded entirely
- If the mismatch is caused by a known, time-bounded event (e.g., a deployment that was rolled back), the affected window may be excluded if it can be cleanly isolated

Both approaches require careful validation and should be treated as producing lower-confidence results than a clean experiment.

**Step 5: Re-run the experiment**
In most cases, the correct resolution is to fix the root cause and re-run the experiment from scratch with a clean traffic allocation. The experiment should not be re-run until the cause has been identified and confirmed as resolved.

---

## SRM as a Blocking Condition

SRM should be treated as a hard block on any Ship or Kill decision:

- A Ship decision made on an SRM-affected result may deploy a change whose true effect is unknown — the measured lift may not be real
- A Kill decision made on an SRM-affected result may abandon a change that would have succeeded under valid conditions
- An Extend decision is only valid if the SRM has been resolved — extending an experiment with an ongoing assignment failure will not produce a valid result at any sample size

In the Ship / Kill / Extend framework, SRM maps directly to **Escalate**: the result cannot be acted upon until the validity of the experiment has been confirmed or the experiment has been re-run.

---

## Anti-Patterns

- **Proceeding with analysis despite a flagged SRM:** The most consequential error. SRM is not a soft warning — it is a validity failure. No metric output from the experiment is reliable.
- **Attempting statistical correction of SRM:** Reweighting or subsetting does not restore causal validity. The result remains untrustworthy.
- **Attributing SRM to random chance:** At p < 0.01, a traffic split imbalance is not random noise. SRM always has a cause; the cause must be found.
- **Re-running without diagnosing the cause:** An unresolved root cause will produce SRM in the re-run. Diagnosis is not optional.
- **Checking for SRM only at experiment end:** SRM should be checked within the first 24–48 hours of an experiment going live, and again at regular intervals. Early detection allows the experiment to be paused before large volumes of invalid data accumulate.

---

## SRM Monitoring Schedule

| Checkpoint | Action |
|---|---|
| 24–48 hours after launch | Run chi-square check on observed vs. expected split. Pause if SRM confirmed. |
| At each scheduled analysis point | Re-run chi-square check before interpreting any metric results. |
| At experiment end | Final SRM check before producing the result summary. All metric analysis is conditional on SRM passing. |
