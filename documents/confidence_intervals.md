# Confidence Intervals: How to Read and Communicate Them in A/B Testing

## Definition

A **confidence interval (CI)** is a range of plausible values for the true effect of a treatment, estimated from sample data. In practice, treat the CI as the range of effect sizes the data cannot rule out — it tells you **where the true effect likely lives and how precisely it has been measured**. It is the primary tool for assessing whether a statistically significant result is also practically meaningful.

**On the frequentist interpretation:** A 95% CI does **not** mean there is a 95% probability the true value falls within this specific interval — the true value either does or doesn't. The 95% refers to the long-run procedure: if the experiment were repeated many times, 95% of the constructed intervals would contain the true parameter. This distinction matters when communicating results — see the interpretation anti-patterns below.

------

## Anatomy of a Confidence Interval

A CI is reported as: **[lower bound, upper bound]** around a point estimate.

**Example:** Conversion rate lift = +1.2 percentage points, 95% CI [+0.4, +2.0]

This means:

- The best single estimate of the lift is +1.2pp
- The true lift is plausibly anywhere from +0.4pp to +2.0pp
- The entire interval is positive → directionally consistent, statistically significant

------

## Reading the Interval: Four Diagnostic Checks

**1. Does the interval cross zero (or the null value)?**

- Entirely positive → statistically significant positive effect
- Entirely negative → statistically significant negative effect
- Crosses zero → not statistically significant; the data are consistent with no effect

**2. What is the width of the interval?**

- Narrow CI → high precision; the estimate is reliable
- Wide CI → low precision; typically caused by small sample size or high variance. A wide CI on a significant result should be treated with caution — the true effect could be much smaller than the point estimate.

**3. Where is the worst-case bound?**

- For a positive lift, examine the **lower bound**. If the lower bound is above your minimum detectable effect (MDE) or commercial threshold, the result is robustly significant. If the lower bound is near zero, the result is significant but fragile.
- For a negative result, examine the **upper bound** for the same reason.

**4. What is the practical range of the interval?**

- Even if the interval excludes zero, ask: is the *entire plausible range* commercially meaningful? CI [+0.01%, +0.03%] is significant but may not be actionable regardless of p-value.

------

## Common Scenarios and How to Interpret Them

| Result                    | CI             | Interpretation                                               |
| ------------------------- | -------------- | ------------------------------------------------------------ |
| Lift = +1.5pp, p = 0.01   | [+0.8, +2.2]   | Strong result. Entire interval above zero and above likely MDE. |
| Lift = +1.5pp, p = 0.04   | [+0.05, +2.95] | Technically significant but wide. Lower bound is near zero — treat with caution. |
| Lift = +0.02pp, p = 0.003 | [+0.01, +0.03] | Highly significant but commercially meaningless. Large sample inflating power. |
| Lift = +0.8pp, p = 0.12   | [−0.2, +1.8]   | Not significant. Interval crosses zero — cannot rule out no effect or harm. |
| Lift = −0.6pp, p = 0.03   | [−1.1, −0.1]   | Significant regression. Shipping this variant would likely cause harm. |

------

## Relationship to P-Values

The CI and p-value are mathematically linked but communicate different things:

- A result is significant at p < 0.05 **if and only if** the 95% CI excludes zero
- The p-value answers: *"Is this effect real?"*
- The CI answers: *"How large is the effect, and how confident are we?"*

**The CI should be the primary output reported** — it contains everything the p-value communicates, plus magnitude and precision. A p-value without a CI strips out the information needed to make a business decision.

**Note:** In some test configurations — particularly one-tailed tests, ratio metrics, or small samples — the CI and p-value may appear to conflict due to rounding, asymmetry in the underlying distribution, or differences in how the test statistic is computed. If a result shows p < 0.05 but the reported CI includes zero, or vice versa, flag for manual review rather than resolving the conflict by defaulting to one measure.

------

## Sample Size and CI Width

CI width is directly controlled by sample size. Larger samples produce narrower intervals:

- Doubling sample size reduces CI width by approximately 30%
- An underpowered experiment produces wide CIs that are difficult to act on even when significant
- When a CI is very wide, the appropriate response is often **to continue the experiment**, not to decide on the current interval

This is why pre-experiment power calculations matter: they define the sample size needed to produce a CI narrow enough to distinguish a meaningful effect from noise.

------

## Interpretation Anti-Patterns

**Avoid when interpreting or reporting CIs:**

- Reporting the point estimate without the interval
- Describing a wide-CI result as "strong" because p < 0.05
- Treating CI width as a significance indicator — it measures precision, not significance
- Stating "there is a 95% probability the true value is in this range" — see Definition

**When escalating or flagging for review, note:**

- Whether the lower bound clears the MDE threshold
- Whether the interval is wide relative to the effect size (imprecise estimate)
- Whether the interval is consistent across primary and secondary metrics

------

## When a CI Should Block a Ship Decision

Flag for further review rather than acting on a CI when:

- The interval is wide enough that the lower bound falls below the commercial threshold, even if the point estimate looks strong
- The interval crosses zero in any segment of the experiment timeline (peeking concern)
- The CI for a guardrail metric (e.g., revenue per user, session depth) includes meaningful negative values, even if the primary metric CI is positive