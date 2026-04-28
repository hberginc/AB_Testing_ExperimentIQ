# Minimum Detectable Effect (MDE): Definition, Business Grounding, and Sample Size Planning

## Definition

The **Minimum Detectable Effect (MDE)** is the smallest effect size that an experiment is designed to detect with a specified level of statistical power. It is the lower bound of commercially meaningful change, the threshold below which a measured effect, even if real, would not justify the cost of shipping the variant.

The MDE is a **design input**, not a statistical output. It is set before the experiment runs, based on business judgment about what magnitude of change is worth detecting. It determines the required sample size: smaller MDEs require more traffic; larger MDEs require less. An experiment cannot reliably detect effects smaller than its MDE regardless of how long it runs.

The MDE answers the question: *"What is the smallest improvement that would actually matter to this business?"*, not *"What effect size does this dataset have the power to detect?"* These are different questions, and conflating them is the most consequential MDE error in A/B testing practice.

---

## Why the MDE Must Be Business-Driven

### The Core Principle

The MDE must be set by business judgment before data collection begins. It must not be derived from observed data, from historical effect sizes in similar experiments, or from what the available traffic can detect. Each of these derivation methods produces an MDE that is wrong in a specific and damaging way.

### What Goes Wrong When MDE Is Data-Derived

**Deriving MDE from available traffic:**
The most common error. The reasoning runs: "We have 50,000 users per week, so we can run a two-week experiment with 100,000 users, what MDE does that give us?" This inverts the correct logic. The question is not what MDE the available traffic can support, it is whether the available traffic is sufficient to detect the MDE the business requires. If the traffic-implied MDE is 5% relative lift but the business only cares about changes of 10% or more, the experiment is over-powered for its purpose. If the traffic-implied MDE is 2% but a 0.5% lift would be commercially meaningful, the experiment is under-powered.

Traffic is a constraint on what experiments are feasible, not a determinant of what effects are worth detecting.

**Deriving MDE from historical experiment results:**
Using the average effect size from past experiments to set the MDE for a new one conflates descriptive history with prescriptive standards. Past experiments may have been measuring the wrong things, may have been underpowered themselves, or may have been subject to novelty effects. The MDE is a forward-looking business standard, not a statistical summary of the past.

**Deriving MDE from the observed effect after the experiment:**
Calculating a post-hoc MDE based on the observed effect size and declaring the experiment "adequately powered" is circular and invalid. Post-hoc power calculations do not validate an experiment, they restate the observed result in different units. If the experiment was not powered against a pre-specified MDE, the power claim is meaningless.

### How to Set the MDE Correctly

The MDE should be set by answering one or more of the following business questions before the experiment launches:

**Revenue impact threshold:** What absolute or relative improvement in the primary metric would produce a commercially meaningful revenue change at current traffic volume? An experiment on a checkout flow might target a 1 percentage point conversion rate lift because that corresponds to a defined revenue threshold at current scale.

**Cost of change threshold:** What improvement is needed to justify the engineering cost, opportunity cost, and risk of shipping the variant? A back-end refactor that produces a 0.1% lift is not worth shipping regardless of significance; the MDE should be set above that threshold.

**Strategic significance threshold:** What effect size would be considered a meaningful result in the context of the product area's goals? A feature designed to increase retention should define "meaningful" in terms of the retention rate change that matters to the growth model, not in terms of what is statistically detectable.

The output of this process is a single number, an absolute or relative effect size, that becomes the MDE for the experiment. It is documented before launch and does not change based on what the experiment finds.

---

## How to Use MDE in Sample Size Planning

### The Four-Parameter Relationship

Sample size is determined by four inputs, of which MDE is the most influential:

- **MDE:** The target effect size. Smaller MDEs require exponentially more sample.
- **Baseline rate:** The current value of the primary metric in the control population (e.g., current conversion rate of 4.0%).
- **α:** The significance threshold. Conventionally 0.05 for a two-tailed test.
- **Power (1 − β):** The probability of detecting the MDE if it exists. Conventionally 0.80; use 0.90 for high-stakes decisions.

Given these four inputs, the required sample size per variant for a two-proportion z-test is approximately:

n = 2 × [ (z_α/2 + z_β)² × p(1−p) ] / δ²

Where:
- z_α/2 = 1.96 for α = 0.05 two-tailed
- z_β = 0.84 for power = 0.80
- p = baseline conversion rate
- δ = absolute MDE (e.g., 0.01 for a 1 percentage point lift)

Total required traffic = n × number of variants.

### Worked Example

**Scenario:** Checkout flow experiment. Baseline conversion rate: 4.0%. Business-defined MDE: 1 percentage point absolute lift (4.0% → 5.0%). α = 0.05, power = 0.80, two variants (control + variant).

n = 2 × [ (1.96 + 0.84)² × 0.04 × 0.96 ] / (0.01)²
n = 2 × [ 7.84 × 0.0384 ] / 0.0001
n = 2 × 0.301 / 0.0001
n ≈ 6,017 per variant → **~12,034 total users required**

If the site receives 2,000 users per day through the checkout flow, the experiment requires approximately **6 days** to reach the required sample size.

### Translating Sample Size to Duration

Required duration = (n per variant × number of variants) / daily traffic through the experiment surface

Duration must account for:
- **Day-of-week effects:** Experiments should run for complete week cycles (multiples of 7 days) to avoid confounding weekday vs. weekend behaviour patterns
- **Ramp-up periods:** If traffic is gradually ramped to the experiment, the ramp period should be excluded from the analysis or accounted for in duration planning
- **Concurrent experiment load:** If multiple experiments are running simultaneously on the same user population, effective traffic per experiment is reduced

---

## Why a Low MDE Requires More Traffic

### The Inverse Relationship

The relationship between MDE and required sample size is inverse and non-linear. As the MDE decreases, required sample size increases, and it does so at a rate proportional to the square of the MDE reduction.

Halving the MDE (detecting an effect twice as small) requires approximately **four times the sample size**, all else equal.

### The Numbers

Using the checkout flow example above (baseline 4%, α = 0.05, power = 0.80):

| MDE (absolute) | MDE (relative) | Required n per variant | Total users required |
|---|---|---|---|
| 2.0pp | 50% | ~1,500 | ~3,000 |
| 1.0pp | 25% | ~6,000 | ~12,000 |
| 0.5pp | 12.5% | ~24,000 | ~48,000 |
| 0.25pp | 6.25% | ~96,000 | ~192,000 |
| 0.1pp | 2.5% | ~600,000 | ~1,200,000 |

A business that wants to detect a 0.1 percentage point conversion lift requires 100 times more traffic than one willing to detect only a 1 percentage point lift. At 2,000 users per day, detecting a 0.1pp lift would require approximately 600 days, infeasible in practice.

### The Practical Implication: MDE Defines Experiment Feasibility

The MDE is the primary determinant of whether an experiment is feasible at all given available traffic. Before committing to an experiment design, the required sample size must be verified against the realistic traffic available to the experiment surface.

If required sample size exceeds what is achievable in a commercially reasonable timeframe (typically 4–6 weeks maximum for most experiments), the correct response is one of three:

1. **Revise the MDE upward:** Accept that smaller effects cannot be detected with available traffic, and design the experiment to detect only commercially significant effects. This is the preferred response if the original MDE was set too conservatively.
2. **Increase traffic allocation:** Route more of the available traffic through the experiment by expanding the eligible user population or increasing the traffic split percentage.
3. **Accept reduced power:** Run the experiment at lower power (e.g., 0.70 instead of 0.80), accepting a higher false negative rate in exchange for feasibility. This is a deliberate trade-off that must be documented, not an ad-hoc decision made because the sample size calculation was inconvenient.

What is not a valid response: running the experiment anyway with insufficient sample size and treating the result as if it were adequately powered.

---

## MDE and the "Statistically Significant but Practically Meaningless" Failure Mode

The MDE is the primary gate against shipping effects that are statistically real but commercially irrelevant. This failure mode, documented in the Ship / Kill / Extend Framework, occurs when:

- The MDE was set too low (or not set at all), allowing the experiment to be powered for effects smaller than the commercial threshold
- The experiment is heavily overpowered (very large traffic volume), producing significance for trivially small effects
- The MDE is not applied as a second gate after statistical significance

The correct application: after confirming statistical significance, the effect size and CI lower bound must both be evaluated against the pre-registered MDE. A result where the CI upper bound barely exceeds the MDE, or where the point estimate is significant but the CI lower bound is below the MDE, is not a clean Ship signal.

**The MDE is not just a sample size input, it is a post-experiment decision filter.** A significant result that does not clear the MDE should be Killed regardless of p-value.

---

## Anti-Patterns

- **Setting MDE based on what the available traffic can detect:** Inverts the correct logic. Traffic constraints determine feasibility, not the definition of a meaningful effect.
- **Running an experiment without a pre-defined MDE:** Without an MDE, there is no standard for evaluating whether a significant result is commercially meaningful. Statistical significance becomes the de facto decision criterion, which is insufficient.
- **Using the observed effect size to retroactively validate power:** Post-hoc power calculations based on observed effects do not validate the experiment. Power must be calculated against a pre-specified MDE.
- **Setting MDE at the smallest detectable effect rather than the smallest meaningful effect:** These are different quantities. The smallest detectable effect is a function of sample size; the smallest meaningful effect is a function of business value. The MDE should always be the latter.
- **Treating the MDE as a significance threshold rather than a commercial filter:** A result that clears the MDE is not automatically significant; a result that is statistically significant does not automatically clear the MDE. Both gates must be passed independently.

---

## MDE Summary: Key Rules

| Rule | Rationale |
|---|---|
| Set MDE before the experiment launches | Post-hoc MDE is circular and invalid |
| Ground MDE in business value, not traffic | Traffic determines feasibility, not meaning |
| Apply MDE as a post-experiment filter | Statistical significance alone is insufficient |
| Halving the MDE requires ~4× the sample | Non-linear relationship drives feasibility planning |
| CI lower bound must clear MDE, not just point estimate | Point estimates overstate the worst-case effect |
| Document MDE in the experiment spec | Missing MDE is a pre-registration failure |
