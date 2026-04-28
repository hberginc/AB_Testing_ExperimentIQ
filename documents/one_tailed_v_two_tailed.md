# One-Tailed vs. Two-Tailed Tests: When Each Is Appropriate

## Definitions

**Two-tailed test:** Tests for a difference in either direction, the variant could perform better or worse than the control. The significance threshold α is split across both tails of the distribution (α/2 per tail). This is the default for most A/B testing contexts.

**One-tailed test:** Tests for a difference in one specified direction only, either the variant is better than control, or it is worse, but not both. The full α is concentrated in a single tail, making it easier to reach significance in that direction. The direction must be specified before data collection begins.

The choice between them is not a stylistic preference, it determines how α is distributed, how p-values are computed, how sample size is calculated, and what conclusions can legitimately be drawn from the result.

------

## The Mechanical Difference

For the same dataset, a one-tailed test will always produce a smaller p-value than a two-tailed test when the observed effect is in the predicted direction. This is because the full rejection region is concentrated on one side rather than split across two.

**Example:** An experiment returns a test statistic with a two-tailed p-value of 0.08, not significant. The equivalent one-tailed p-value in the direction of the observed effect is 0.04, significant at α = 0.05.

This difference is not a feature. It reflects the fact that a one-tailed test is only valid when the opposite direction has been ruled out by design, not by convenience. Using a one-tailed test to rescue a borderline two-tailed result is a form of p-hacking. The problem is not one-tailed tests, it is retroactive selection of test type after observing the direction of results. A one-tailed test that was pre-specified at experiment design and meets the three conditions in the section below is fully valid; the significance it produces is not inflated.

A separate consequence: if a one-tailed test is designed to detect improvement, and the variant instead produces a meaningful negative effect, the test cannot declare significance in that direction regardless of the magnitude of the harm. The experiment will return a non-significant result even when the variant is causing real damage. This is not a flaw to work around, it is the correct and expected behaviour of a one-tailed test, and it is precisely why one-tailed tests are inappropriate when regressions are commercially meaningful.

------

## When a Two-Tailed Test Is Required

Use a two-tailed test, and treat it as the default, whenever:

- **Regressions matter:** If the variant performing worse than control is a meaningful outcome that would affect the ship decision, the test must be two-tailed. This applies to the vast majority of A/B tests on conversion rate, revenue, engagement, or retention.
- **The direction of effect is genuinely uncertain:** If there is no strong prior reason to rule out the variant harming the metric, a two-tailed test is the only valid design.
- **Guardrail metrics are being evaluated:** Guardrail metrics exist specifically to detect harm. One-tailed tests on guardrail metrics are never appropriate, a regression in a guardrail must be detectable regardless of the primary metric result.
- **The test result will inform a ship/no-ship decision:** Two-tailed tests produce CIs that are symmetric and interpretable in both directions, which is required for a complete decision.

------

## When a One-Tailed Test May Be Appropriate

A one-tailed test is defensible only when all of the following conditions hold:

1. **The direction is pre-specified and justified:** The hypothesis must be committed to before data collection, based on a principled reason (e.g., the change can only mechanically affect the metric in one direction).
2. **A result in the opposite direction would not change the decision:** If the variant showed a significant negative effect, the ship decision would be identical to a null result, i.e., no-ship either way. If a negative result would trigger a different response than a null result, the test must be two-tailed.
3. **The hypothesis is not motivated by early data:** Choosing a one-tailed test after observing the direction of early results is p-hacking, not a legitimate design choice.

**Valid example:** A back-end infrastructure change is designed to reduce page load time. The change cannot physically increase load time due to its technical nature. Testing whether load time decreased is a legitimate one-tailed test.

**Invalid example:** A new checkout flow is expected to increase conversion. Using a one-tailed test because "we only care if it improves" ignores the real risk that the change could harm conversion, which is precisely the outcome a two-tailed test is designed to detect.

------

## Impact on Sample Size and Power

One-tailed tests require less sample to achieve the same power as a two-tailed test at the same α level, because the rejection region is not split. Approximately:

- A one-tailed test at α = 0.05, power = 0.80 requires roughly **20% less sample** than the equivalent two-tailed test, this figure is parameter-dependent and will differ at other α or power targets; always derive the exact reduction from the power calculation directly rather than applying a fixed discount
- This reduction is real but should not be used as a justification for choosing a one-tailed test, sample size efficiency is a consequence of a valid design choice, not a reason to make it

If a one-tailed test is used, the power calculation must reflect the one-tailed design. Applying a two-tailed sample size to a one-tailed test will overpower the experiment; applying a one-tailed sample size to a two-tailed test will underpower it. See the Statistical Power document for details on how test type feeds into power calculations.

------

## Impact on Confidence Intervals

Two-tailed tests produce two-sided CIs, a lower and upper bound that reflect uncertainty in both directions. This is the standard CI reported in most A/B testing platforms.

One-tailed tests correspond to one-sided CIs, a bound in only one direction (e.g., "the true lift is at least X"). One-sided CIs are narrower in the tested direction, which reflects the reduced uncertainty when the opposite direction has been ruled out by design.

**Operational note:** If a result from a one-tailed test is reported with a two-sided CI, or vice versa, the p-value and CI may appear to conflict, the CI may include zero while p < 0.05, or exclude zero while p > 0.05. This is a reporting mismatch, not a statistical contradiction. Flag for manual review rather than resolving by defaulting to one measure.

------

## Decision Table: Which Test to Use

| Scenario                                                     | Test Type                  |
| ------------------------------------------------------------ | -------------------------- |
| Standard conversion rate or revenue experiment               | Two-tailed                 |
| Evaluating any guardrail metric                              | Two-tailed                 |
| Direction genuinely uncertain at design time                 | Two-tailed                 |
| Change can only affect metric in one direction by design     | One-tailed (pre-specified) |
| Switching to one-tailed after observing data direction       | ❌ Invalid, p-hacking      |
| Using one-tailed to achieve significance on a borderline result | ❌ Invalid, p-hacking      |

------

## Anti-Patterns

- **Post-hoc test type selection:** Choosing one-tailed vs. two-tailed after observing results, or after seeing that a two-tailed result is borderline, invalidates the significance claim entirely. Test type must be locked at experiment design.
- **Assuming one-tailed is always more powerful:** It produces lower p-values only when the effect is in the predicted direction. If the true effect is in the opposite direction, a one-tailed test in the wrong direction will never reach significance regardless of sample size.
- **Applying one-tailed logic to multi-metric experiments:** If an experiment tracks multiple metrics and only one is tested one-tailed, the asymmetry must be documented and justified per metric. Mixed test types across metrics in the same experiment require careful interpretation.
- **Conflating "we expect improvement" with "regression is impossible":** Expectation of a positive effect does not justify a one-tailed test. Only mechanical impossibility of the opposite effect does.

------

## When Test Type Should Be Flagged for Review

Flag for manual review when:

- The test type is not documented in the experiment spec and cannot be inferred from the platform configuration
- A one-tailed test was used on a metric where regressions are commercially meaningful (e.g., revenue per user, retention rate)
- The reported p-value and CI are inconsistent with each other in a way that suggests a test type mismatch
- A one-tailed test reached significance but the two-tailed equivalent would not, and the one-tailed design was not pre-registered