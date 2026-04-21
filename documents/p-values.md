# P-Values: Operational Reference for A/B Test Interpretation

## Definition

A **p-value** is the probability of observing results at least as extreme as those measured, assuming the null hypothesis (no difference between variants) is true. It is a measure of evidence against chance — not a measure of effect size, importance, or business value.

------

## The Decision Threshold

The conventional threshold is **p < 0.05**, meaning there is less than a 5% probability the observed difference arose by random chance.

- **p < 0.05** → Statistically significant. The result is unlikely to be noise.
- **p ≥ 0.05** → Not statistically significant. Insufficient evidence to reject the null hypothesis.

**Important:** p = 0.05 is a convention, not a law. Treat borderline results (e.g., p = 0.048 vs. p = 0.052) with equivalent caution — a result does not become meaningful by crossing an arbitrary line. Results near the threshold should trigger further review rather than a direct ship/no-ship decision.

------

## One-Tailed vs. Two-Tailed Tests

P-value interpretation depends on the test type:

- **Two-tailed test**: Detects differences in *either* direction (variant better *or* worse). Standard for most A/B tests where regressions matter.
- **One-tailed test**: Detects differences in *one* direction only. Produces a smaller p-value for the same data — appropriate only when a negative outcome is explicitly out of scope.

Always confirm which test was run before interpreting significance.

------

## Statistical Significance ≠ Practical Significance

A statistically significant result may have no commercial value. With large sample sizes, even trivially small effects will produce p < 0.05.

**Example:** A checkout flow experiment on 2 million users shows a conversion rate lift from 4.00% to 4.04% with p = 0.003. The result is statistically significant, but a 0.04 percentage point lift may not justify the engineering cost or the risk of shipping.

Always evaluate **effect size and business impact** alongside the p-value. Statistical significance is a threshold for credibility, not a recommendation to act.

------

## Sample Size and P-Value Sensitivity

P-values are directly influenced by sample size. A larger sample increases statistical power, meaning smaller and smaller effects will cross the significance threshold as N grows. In high-traffic experiments, almost any non-zero difference will eventually reach p < 0.05.

This means: **in large experiments, the p-value answers "is this real?" but not "does this matter?"** Use pre-registered minimum detectable effects (MDEs) and confidence intervals to bound what the result actually means in practice.

------

## What a P-Value Does NOT Tell You

| Question                                 | Does the p-value answer it?                           |
| ---------------------------------------- | ----------------------------------------------------- |
| Is the effect large enough to matter?    | ❌ No — check effect size and confidence interval      |
| Should we ship this change?              | ❌ No — requires business context                      |
| Is the null hypothesis true if p ≥ 0.05? | ❌ No — absence of evidence is not evidence of absence |
| Is this finding reproducible?            | ❌ No — a single p < 0.05 is not confirmation          |

------

## Multiple Comparisons

When multiple metrics are tested simultaneously in a single experiment, the probability of observing at least one false positive increases with each additional test. A p < 0.05 threshold on a primary metric is reliable, but the same threshold applied to five secondary metrics means your effective false positive rate is significantly higher than 5%.

When interpreting experiments with multiple metrics, treat secondary metric significance as directional signal rather than confirmation. If a secondary metric drives the ship decision, flag this explicitly — the result warrants additional scrutiny or a follow-up experiment to confirm.

------

## When to Escalate Rather Than Decide

A p-value alone should trigger further review — rather than a direct decision — when:

- The result is borderline (p between 0.04 and 0.07)
- The effect size is statistically significant but below the pre-defined MDE
- The test was underpowered or ended early
- Significance appeared in a secondary metric but not the primary

When escalation conditions are met, the recommended actions are: extend the test if sample size is the issue, request analyst review if the result is borderline or conflicts across metrics, or reframe the decision around the confidence interval range rather than the binary significance threshold.

