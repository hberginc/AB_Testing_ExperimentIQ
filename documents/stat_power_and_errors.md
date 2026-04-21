# Statistical Power and Type I/II Errors in A/B Testing

## Definitions

**Type I Error (False Positive):** Concluding a real effect exists when it does not. The experiment detects a difference between control and variant that is, in fact, noise. Controlled by the significance threshold α — conventionally set at 0.05, meaning a 5% tolerance for false positives.

**Type II Error (False Negative):** Failing to detect a real effect that does exist. The experiment returns a non-significant result despite a true difference between variants. Controlled by statistical power — the probability of correctly detecting a real effect when one exists.

**Statistical Power:** The probability that an experiment will detect a true effect of a given size, at a given sample size and α level. Conventionally targeted at **0.80**, meaning a 20% tolerance for false negatives (β = 0.20).

Power is not a post-hoc diagnostic — it is a pre-experiment input. An experiment should be designed to achieve adequate power before data collection begins.

------

## The Four Possible Outcomes of Any Experiment

|                               | Effect is Real                   | No Effect Exists                  |
| ----------------------------- | -------------------------------- | --------------------------------- |
| **Result is Significant**     | ✅ True Positive (correct ship)   | ❌ Type I Error (false positive)   |
| **Result is Not Significant** | ❌ Type II Error (false negative) | ✅ True Negative (correct no-ship) |

The error rates are set by design choices made before the experiment runs — α controls the column on the right, power controls the column on the left.

------

## The Relationship Between Power, Sample Size, and MDE

These four quantities are mathematically linked. Fixing any three determines the fourth:

- **α (significance threshold):** Typically 0.05. Lowering α (stricter) reduces false positives but requires larger samples to maintain power.
- **Power (1 − β):** Typically 0.80. Higher power (e.g., 0.90) reduces false negatives but requires larger samples.
- **MDE (minimum detectable effect):** The smallest effect size worth detecting commercially. Smaller MDEs require larger samples.
- **Sample size:** The output of the power calculation given the three inputs above.

**The key implication:** An experiment cannot be evaluated in isolation from its power design. A non-significant result in an underpowered experiment is uninformative — it may reflect a real null effect or simply insufficient sample size to detect the true effect.

------

## Underpowered Experiments: What Goes Wrong

An underpowered experiment is one where sample size is insufficient to reliably detect the target MDE. Consequences:

- **Inflated false negative rate:** True effects go undetected; valid improvements are abandoned
- **Inflated effect size estimates on significant results:** When power is low, the only results that cross the significance threshold tend to be those where random variation pushed the estimate upward — this is winner's curse. Significant results from underpowered experiments systematically overestimate true effect sizes.
- **Wide confidence intervals:** The CI will be too wide to distinguish a meaningful effect from noise, even when the point estimate looks promising

An experiment that ends early due to business pressure, or that was sized based on available traffic rather than required power, should be treated as underpowered by default.

------

## Overpowered Experiments: A Separate Risk

Overpowering — running far more traffic than needed — produces its own distortions:

- Trivially small effects reach statistical significance, creating pressure to ship changes with no commercial value
- p-values become very small for effects that are real but irrelevant, which can mislead automated decision systems
- Resources (traffic, time, engineering) are allocated inefficiently

Overpowering is less dangerous than underpowering but is not neutral. The MDE should reflect a commercially meaningful threshold, not the smallest detectable noise.

------

## Power Calculation Inputs for A/B Testing

A standard pre-experiment power calculation requires:

- **Baseline conversion rate:** The current rate of the primary metric in the control population
- **MDE:** The minimum relative or absolute lift worth detecting
- **α:** Significance threshold (default 0.05)
- **Target power:** Conventionally 0.80; use 0.90 for high-stakes or irreversible decisions
- **Number of variants:** Each additional variant increases the multiple comparisons burden and reduces effective power per comparison. When running experiments with more than one variant, the significance threshold α must be adjusted downward — for example, using a Bonferroni correction — to keep the experiment-wide false positive rate at 0.05. Failing to adjust inflates the probability of at least one spurious significant result across the variants.
- **Test type (one-tailed vs. two-tailed):** One-tailed tests concentrate the rejection region in a single direction, requiring less sample size to achieve the same power as a two-tailed test at the same α level. Power calculations must specify which test type will be used — applying a two-tailed sample size to a one-tailed test, or vice versa, will produce an incorrectly sized experiment.

The output is the **required sample size per variant**. Total required traffic is this number multiplied by the number of variants.

------

## Interpreting Results in the Context of Power

When a result is **not significant**, the power of the experiment determines what that means:

- **Adequately powered + not significant:** Strong evidence the true effect is smaller than the MDE. A reasonable basis for a no-ship decision.
- **Underpowered + not significant:** Inconclusive. The experiment cannot distinguish between "no effect" and "effect too small to detect." Do not treat as evidence of null.

When a result **is significant** from an underpowered experiment:

- The effect size estimate is likely inflated (winner's curse)
- Replicate before acting, or apply a discount to the point estimate
- Verify the CI lower bound still clears the commercial threshold after discounting

------

## Common Anti-Patterns

- **Sizing experiments based on available traffic, not required power:** Produces underpowered tests by default. Power must be calculated first; traffic allocation follows.
- **Stopping early when significance is reached:** Inflates Type I error rate. Pre-register a fixed sample size and do not evaluate significance until it is reached, unless a sequential testing framework is in place.
- **Treating a non-significant result as proof of no effect:** Absence of significance is not evidence of absence — it is only evidence of absence if the experiment was adequately powered.
- **Using α = 0.05 as a universal default for all decisions:** High-stakes or irreversible decisions warrant stricter α (e.g., 0.01). Low-stakes or easily reversible changes may tolerate α = 0.10.

------

## When Power Concerns Should Block or Modify a Decision

Flag for review rather than acting on results when:

- Post-hoc power analysis (given observed effect size and sample size) reveals power was below 0.70 — representing a meaningful degradation from the 0.80 target and a false negative rate above 30%
- The experiment was stopped before reaching the pre-registered sample size
- The result is significant but the CI is wide enough that the lower bound falls below the MDE — consistent with winner's curse in a low-power design
- The experiment ran at reduced traffic allocation (e.g., 10% / 10% split) without a corresponding recalculation of required duration