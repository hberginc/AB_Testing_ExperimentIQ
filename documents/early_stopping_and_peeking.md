# Early Stopping and Peeking: Why Timing Invalidates Results

## Definition

**Peeking** is the practice of evaluating experiment results before the pre-registered sample size or duration has been reached. **Early stopping** is acting on those results, making a Ship, Kill, or Extend decision based on an interim read.

Both are validity threats. Peeking inflates the false positive rate even when no action is taken, because repeated evaluation of accumulating data increases the probability of observing a spuriously significant result by chance. Early stopping compounds this by locking in a decision at the moment the data happens to look most favourable, which is systematically not the same moment as when the data is most accurate.

The core principle this document establishes: **an experiment's planned sample size and duration are fixed at design time and are not subject to revision based on interim results.** The only legitimate exception is a pre-registered sequential testing framework.

---

## Why Peeking Inflates False Positives

### The Mechanism

A significance test at α = 0.05 guarantees a 5% false positive rate for a single test on a complete dataset. This guarantee does not extend to repeated testing of the same accumulating dataset.

Each time results are evaluated during an experiment, there is a chance the data will cross the significance threshold by random variation, even when no true effect exists. The more frequently results are checked, the higher the probability that at least one check will produce p < 0.05 by chance. This is not a flaw in any individual test, it is a consequence of applying a fixed-sample test to a sequential data collection process.

### The Inflation in Numbers

Under repeated peeking, the effective false positive rate departs substantially from the nominal α = 0.05:

| Number of Interim Looks | Effective False Positive Rate (approx.) |
|---|---|
| 1 (no peeking) | 5.0% |
| 2 | ~8% |
| 5 | ~14% |
| 10 | ~19% |
| 20 | ~25% |

An experiment checked daily over a four-week period, a common practice, can produce an effective false positive rate approaching 25–30%, meaning roughly one in four significant results is noise. The experiment appears to be operating at α = 0.05 but is functionally operating at α = 0.25 or higher.

### Why Early Significant Results Are Especially Unreliable

Random variation in conversion rates and other metrics is highest early in an experiment, when sample sizes are small and estimates are imprecise. A significant result observed at 20% of the planned sample size is far more likely to be noise than a significant result observed at 100%, not because the significance threshold has changed, but because the signal-to-noise ratio in the data has not yet stabilised.

Stopping at the moment significance is first observed selects for the noisiest, least stable estimates. This produces systematic overestimation of effect sizes, the same winner's curse dynamic described in the Statistical Power document, applied to timing rather than sample size.

---

## What Sequential Testing Is

Sequential testing is a family of statistical methods designed to allow valid interim analysis of experiment results. Unlike fixed-sample tests, sequential tests account for the fact that data is being evaluated multiple times, and adjust the significance threshold at each look to maintain the experiment-wide false positive rate at the intended α level.

### How It Works

Sequential testing frameworks pre-specify:
- The number and timing of interim looks (or a continuous monitoring boundary)
- An adjusted significance threshold at each look, typically more stringent than α = 0.05 at early looks, becoming less stringent as the experiment approaches its planned end
- The conditions under which early stopping is valid, either for efficacy (strong positive result) or futility (result is clearly not going to reach significance)

Common sequential testing approaches include the **sequential probability ratio test (SPRT)**, **alpha spending functions** (e.g., O'Brien-Fleming boundaries), and **always-valid p-values** as implemented in some modern experimentation platforms.

### What Sequential Testing Is Not

Sequential testing is not a licence to stop whenever results look good. It is a pre-registered framework that defines in advance the exact conditions under which interim stopping is valid. The following do not constitute sequential testing:

- Checking results daily and stopping when p < 0.05 is first observed
- Deciding to stop "because the result is obvious" based on a large point estimate
- Applying a Bonferroni correction to the number of looks as a post-hoc adjustment
- Using a sequential testing framework that was not pre-registered before the experiment began

If a sequential testing framework is not in place before the experiment launches, interim results have no decision-making validity. The experiment must run to its planned duration.

---

## The Guardrail Rule: Never Stop Before Planned Duration

This is a hard operational rule with one defined exception:

> **An experiment must not be stopped, and its results must not be acted upon, before the pre-registered sample size or duration has been reached, unless a sequential testing framework was registered before the experiment began.**

### Why This Rule Exists

The planned sample size is not arbitrary. It is the output of a power calculation that defines the minimum data required to distinguish a real effect from noise at the target MDE, α, and power level. Stopping before this threshold is reached means the experiment has not yet collected the evidence required to support a reliable conclusion, regardless of what the interim data shows.

A significant result before planned duration is consistent with three explanations:
1. The effect is real and the experiment detected it early (true positive)
2. The result is a false positive inflated by peeking (type I error)
3. The effect size is being overestimated due to early noise (winner's curse)

These three explanations cannot be reliably distinguished from interim data. Only completing the planned run produces data that can discriminate between them.

### The Business Pressure Problem

Early stopping is most commonly triggered not by statistical reasoning but by business pressure, a stakeholder sees an interim significant result and wants to ship immediately. This pressure is understandable but must be resisted as a hard rule, for two reasons:

First, the interim result is not reliable evidence of a true effect. A significant result that would have reversed or disappeared by planned completion is common, not rare, particularly in the first half of an experiment's planned duration.

Second, allowing business pressure to override planned duration creates a systematic bias across the entire experimentation programme. If experiments are stopped early when they look positive, the set of "successful" experiments will be systematically over-inflated with false positives and upward-biased effect estimates. Over time, this degrades the reliability of the programme as a whole.

### Legitimate Reasons to Stop Early

The following are the only conditions under which stopping before planned duration is valid:

- **A pre-registered sequential testing boundary has been crossed:** The framework was in place before the experiment launched and the interim look was pre-specified. This is not peeking, it is planned analysis.
- **A confirmed safety or harm event:** The variant is causing clear, significant harm to a critical guardrail metric (e.g., severe revenue regression, user-facing errors) and continuing the experiment would cause material damage. This is an emergency stop, not a statistical decision, and should be treated as an invalid experiment result requiring a re-run.
- **A confirmed experiment validity failure:** SRM, data pipeline failure, or platform misconfiguration has been detected. Stopping to resolve the validity issue is correct, the experiment must be re-run, not analysed from the invalid data.

None of these conditions include "the result looks significant and we want to ship faster."

---

## Impact on the Experiment Corpus

Early stopping, if it occurs, has downstream effects on every experiment that follows:

- **Effect size estimates are inflated:** Stopping at peak noise overestimates lift, creating unrealistic benchmarks for future experiments
- **False positive rate accumulates:** A programme that routinely stops early will accumulate more shipped variants with no true effect, degrading the signal-to-noise ratio of post-ship monitoring
- **Power calculations become unreliable:** If experiments routinely stop at 60–70% of planned sample, future power calculations based on historical effect sizes will systematically overestimate detectable effects

For an automated decision system, early stopping is particularly dangerous because the inflation is invisible in the result data, a result that was stopped early looks identical to a result that ran to completion, unless the stopping condition is explicitly recorded and checked.

---

## Detection: How to Identify a Peeking-Affected Result

An automated system should flag results as potentially peeking-affected when:

- The experiment end date is earlier than the date implied by the pre-registered sample size and traffic allocation
- The result is significant and the achieved sample size is less than 80% of the pre-registered target
- The experiment log shows significance was first reached early in the run and the experiment was ended shortly after
- No sequential testing framework is documented in the experiment spec but the experiment was stopped before planned duration

When any of these conditions are present, the result should be escalated rather than acted upon. A peeking-affected result is not automatically invalid, but it requires human review to assess whether the early stop was legitimate before a decision is made.

---

## Anti-Patterns

- **Stopping when p < 0.05 is first observed:** The most common form of peeking. The first time a result crosses the significance threshold is the least reliable moment to act on it.
- **"We'll just check to see how it's going":** Informal peeking without intent to stop still inflates the false positive rate if the check influences any downstream decision about the experiment.
- **Extending an experiment after a non-significant interim result to wait for significance:** The mirror image of early stopping. Extending beyond planned duration in search of significance is also a validity violation, it is p-hacking in the other direction.
- **Applying a post-hoc correction for multiple looks:** Adjusting for peeking after the fact does not restore the validity of the result. Sequential corrections must be pre-registered.
- **Treating a stopped experiment as valid because the effect "held up" in post-ship monitoring:** Post-ship monitoring is not a substitute for a valid experiment. Correlation in post-ship data does not restore the causal validity that early stopping compromised.

---

## Summary: Valid vs. Invalid Stopping Conditions

| Stopping Reason | Valid? |
|---|---|
| Planned sample size reached | ✅ Valid |
| Pre-registered sequential boundary crossed | ✅ Valid |
| Confirmed safety/harm event on critical guardrail | ✅ Valid (emergency stop, re-run required) |
| SRM or experiment validity failure detected | ✅ Valid (re-run required) |
| Interim result is significant (p < 0.05) | ❌ Invalid |
| Business stakeholder wants to ship faster | ❌ Invalid |
| Result "looks obvious" from the point estimate | ❌ Invalid |
| Team has high conviction the variant will win | ❌ Invalid |
| Extending past planned duration to find significance | ❌ Invalid |
