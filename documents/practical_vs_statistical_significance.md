# Practical Significance vs. Statistical Significance

## Definition

**Statistical significance** answers one question: is the measured effect likely to be real, or is it consistent with random noise? It is controlled by the p-value and the significance threshold α. A result is statistically significant when the probability of observing an effect at least this large by chance — under the null hypothesis of no effect — falls below α.

**Practical significance** answers a different question: is the measured effect large enough to matter? It is evaluated against the MDE, the commercial impact of the effect size, the cost of shipping the variant, and any user experience trade-offs the change introduces. A result is practically significant when the effect size justifies the decision to ship — independently of whether the result is statistically significant.

These two conditions are independent. A result can be:
- Statistically significant and practically significant → the standard Ship signal
- Statistically significant but not practically significant → the most consequential failure mode in high-traffic experimentation
- Not statistically significant but potentially practically significant → an underpowered experiment that may be worth re-running with more traffic
- Neither → a confirmed null with no commercial relevance

The Ship / Kill / Extend decision requires both conditions to be evaluated. Statistical significance is the first gate — it establishes that the effect is real. Practical significance is the second gate — it establishes that the effect is worth acting on. An automated decision system that applies only the first gate will systematically ship changes with no commercial value.

---

## Why Statistical Significance Does Not Imply Practical Significance

### The Mechanism

Statistical significance is a function of three quantities: effect size, sample size, and variance. For a fixed effect size, increasing the sample size will always eventually produce a statistically significant result — even when the effect is commercially irrelevant. This is not a flaw in the test; it is the correct behaviour of a test designed to distinguish signal from noise. The problem arises when the test is treated as answering a business question it was not designed to answer.

In high-traffic environments — e-commerce platforms, consumer applications, search engines — experiments routinely run on millions of users. At this scale, the statistical machinery is sensitive enough to detect effects that are orders of magnitude below any commercially meaningful threshold. The result is a category of findings that are rigorously real and rigorously irrelevant.

### The Signal to Watch For

Practical insignificance is most likely when:

- The experiment ran on a very large user population (>500,000 users per variant)
- The p-value is very small (p < 0.01, often p < 0.001) — reflecting high power, not large effect
- The point estimate is small in absolute terms relative to the baseline rate
- The CI is narrow — precision is high, but the precise estimate is of a small effect
- The pre-registered MDE was not set, or was set too conservatively (too small)

A narrow CI around a small point estimate with a very small p-value is the diagnostic fingerprint of a practically insignificant result in an overpowered experiment.

---

## Worked Example: Checkout Conversion Rate

### The Scenario

A consumer e-commerce platform runs an A/B test on its checkout flow. The variant introduces a minor UI refinement — a cosmetic change to the progress indicator. The experiment runs for four weeks on the full user base.

**Experiment parameters:**
- Users per variant: 1,200,000
- Baseline conversion rate (control): 6.000%
- Variant conversion rate: 6.042%
- Absolute lift: +0.042 percentage points
- Relative lift: +0.7%
- p-value: 0.0021
- 95% CI: [+0.016pp, +0.068pp]

### The Statistical Interpretation

The result is statistically significant at p < 0.05. The CI excludes zero. The effect is in the positive direction. A naive analysis — or an automated system evaluating only statistical outputs — would recommend Ship.

### The Practical Interpretation

**Step 1: Evaluate the absolute effect size.**
A 0.042 percentage point lift means that for every 10,000 users who go through checkout, approximately 4 additional conversions are produced. At the platform's current scale of 2,400,000 total experiment users, the estimated incremental conversions over the experiment period are approximately 1,008.

**Step 2: Estimate commercial impact.**
If the average order value is £65, the estimated incremental revenue attributable to the variant over four weeks is approximately £65,520. Annualised at the same traffic volume, that is approximately £850,000.

**Step 3: Evaluate against cost of shipping.**
The UI change requires engineering finalisation, QA, accessibility review, and deployment. Estimated cost: 3 weeks of engineering time. Opportunity cost: 3 weeks of engineering capacity diverted from higher-priority roadmap items. Ongoing maintenance cost of the additional UI complexity.

**Step 4: Apply the MDE filter.**
The pre-registered MDE for this experiment was 0.5 percentage points absolute — the threshold below which the business defined the change as not worth shipping. The observed lift of 0.042pp is approximately 12× below the MDE. The CI upper bound of 0.068pp is also well below the MDE. The effect does not clear the commercial threshold at any point in the plausible range.

**Step 5: Check the CI lower bound.**
The CI lower bound is +0.016pp — the worst-case plausible effect is even smaller than the point estimate. The entire plausible range of the effect falls below the MDE.

### The Correct Decision: Kill

Despite a p-value of 0.0021 and a highly significant result by any conventional statistical standard, the correct decision is Kill. The effect is real — the variant genuinely produces a small lift in conversion rate. The effect is not worth shipping — the lift is too small to justify the engineering cost, opportunity cost, and complexity it introduces.

This is the statistically significant but practically meaningless pattern. The high significance is a consequence of the large sample size (1.2 million users per variant), not of a large effect. The experiment was adequately powered to detect effects far smaller than the MDE — which means it was over-powered for its commercial purpose.

---

## The Three Practical Significance Filters

Every statistically significant result should be evaluated against three filters before a Ship decision is confirmed. All three must pass.

### Filter 1: Effect Size vs. MDE

The point estimate and the CI lower bound must both clear the pre-registered MDE. The point estimate alone is insufficient — it is the best single estimate, but the true effect may be anywhere in the CI. Using the lower bound as the evaluation point is the conservative and correct approach.

- **Point estimate > MDE, CI lower bound > MDE:** Strong practical significance signal. Proceed to filters 2 and 3.
- **Point estimate > MDE, CI lower bound < MDE:** Borderline. The best estimate clears the threshold but the plausible range does not. Escalate rather than Ship automatically.
- **Point estimate < MDE:** Kill. The best estimate of the effect does not reach the commercial threshold, regardless of significance.

### Filter 2: Commercial Impact Assessment

Translate the effect size into business terms appropriate to the experiment context:

- **Revenue impact:** Estimated incremental revenue = effect size × volume × average order value (or equivalent). Evaluate against the cost of shipping (engineering, opportunity cost, ongoing maintenance).
- **Engagement impact:** Estimated incremental sessions, retention events, or feature activations. Evaluate against the strategic value of the improvement and the cost of delivering it.
- **Cost impact:** For efficiency-focused experiments (latency, support rate, error rate), estimate the operational savings against the cost of the change.

A result that clears the MDE but produces a commercial impact below the cost of shipping should be Killed. The MDE is a pre-registered proxy for commercial value — but the commercial impact assessment at analysis time provides a more direct evaluation.

### Filter 3: User Experience Trade-Offs

Statistical and commercial significance do not capture the full cost of a change. Evaluate:

- **Complexity introduced:** Does the variant add UI, logic, or code complexity that will compound over time? A small lift produced by a complex change may not be worth the long-term maintenance cost.
- **User experience regressions not captured by guardrail metrics:** Guardrail metrics are defined in advance and may not capture every dimension of user experience impact. If the variant produces a qualitatively worse experience for a user segment — even without a measurable metric regression — this is a cost that should be weighed.
- **Reversibility:** A change that is difficult to reverse should require stronger practical significance evidence than a change that can be rolled back in hours. The asymmetry of commitment should raise the bar for marginal results.

---

## Relative vs. Absolute Effect Size: A Critical Distinction

Practical significance must be evaluated on **absolute effect size**, not relative lift. Relative lift is a useful summary statistic but is systematically misleading for practical significance assessment in low-baseline contexts.

**Example of the distortion:**

A metric with a baseline rate of 0.10% shows a variant rate of 0.12%. The relative lift is +20% — which sounds commercially meaningful. The absolute lift is +0.02 percentage points — which, at any realistic traffic volume, produces negligible incremental value.

Reporting relative lift without absolute lift in a low-baseline context creates the appearance of a large, practically significant effect from what may be a trivially small absolute change. The MDE should be defined in absolute terms for this reason — it anchors the evaluation to the actual magnitude of the change, not to its ratio relative to a small baseline.

---

## Business Context Factors That Modify the Practical Significance Assessment

Practical significance is not a fixed threshold — it is a judgment that incorporates business context. The following factors can raise or lower the effective bar:

**Strategic priority:** A result that clears the MDE for a high-priority product area may warrant shipping even if the commercial impact calculation is marginal, because the change aligns with a strategic direction that has value beyond the immediate metric lift. Conversely, a strong result in a low-priority area may not warrant the shipping cost.

**Portfolio effects:** A single experiment producing a 0.042pp lift is not worth shipping. If the same variant is one of ten similar UI refinements, each producing small lifts, the aggregate portfolio effect may be meaningful. This is a business judgment, not a statistical one — but it is a legitimate input to the practical significance assessment.

**Competitive and timing factors:** A change that produces a marginal lift today may be worth shipping if it enables future iteration or if competitive dynamics make speed of deployment valuable. These factors do not change the statistical analysis but are valid inputs to the commercial impact assessment.

None of these factors override the MDE filter. They are inputs to the commercial impact assessment (Filter 2) and can inform the Escalate decision when results are borderline.

---

## Anti-Patterns

- **Shipping on statistical significance alone:** The most common and consequential practical significance failure. p < 0.05 is not a Ship signal — it is a credibility threshold that enables the practical significance assessment to begin.
- **Using relative lift to assess commercial impact in low-baseline contexts:** Relative lift inflates the apparent magnitude of small absolute changes. Commercial impact must be calculated from absolute effect size and volume.
- **Setting the MDE at the minimum detectable effect rather than the minimum meaningful effect:** Ensures the experiment will produce practically insignificant significant results at any traffic volume. The MDE must be grounded in business value.
- **Treating a very small p-value as evidence of a large effect:** p-value magnitude reflects sample size and variance as much as effect size. A p-value of 0.0001 in an experiment with 2 million users per variant is not evidence of a large effect — it is evidence of high power.
- **Skipping the commercial impact calculation when the CI clears the MDE:** The MDE is a proxy for commercial value. The direct commercial impact calculation is the more precise evaluation and should always be completed for results near the MDE boundary.

---

## Summary Decision Rules

| Condition | Decision |
|---|---|
| Significant, CI lower bound > MDE, positive commercial impact | Ship |
| Significant, CI lower bound > MDE, commercial impact below shipping cost | Kill (practically meaningless) |
| Significant, point estimate < MDE | Kill (practically meaningless) |
| Significant, point estimate > MDE, CI lower bound < MDE | Escalate (borderline practical significance) |
| Significant, large relative lift, small absolute lift | Kill or Escalate — evaluate absolute effect against MDE |
| Not significant, large practical potential | Extend — inadequate power to assess practical significance |
