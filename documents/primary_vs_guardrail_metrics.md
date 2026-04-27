# Primary vs. Guardrail Metrics: Structuring the Metric Hierarchy

## Definition

A **metric hierarchy** is the pre-registered structure that assigns every tracked metric to a role before the experiment runs. The role determines how the metric's result is used in the Ship / Kill / Extend decision. Without a defined hierarchy, all metrics compete equally for interpretive weight — which is the structural condition that enables p-hacking and post-hoc metric selection.

The three tiers of the metric hierarchy are:

**Primary metric:** The single metric whose result determines the experiment outcome. One primary metric per experiment. Statistical significance is evaluated at α = 0.05 against this metric. A significant positive result on the primary metric is a necessary condition for Ship. A significant negative result is a sufficient condition for Kill.

**Secondary metrics:** Metrics that provide supporting evidence, directional context, or mechanistic explanation for the primary metric result. Secondary metrics are reported alongside the primary but do not independently determine the decision. A significant result on a secondary metric when the primary is not significant is a hypothesis for a future experiment, not a Ship signal.

**Guardrail metrics:** Metrics that must not regress. A significant regression on a guardrail metric is a sufficient condition for Kill or Escalate, regardless of the primary metric result. Guardrail metrics exist to protect against variants that improve one dimension of the product at the cost of another.

---

## The Primary Metric

### Selection Criteria

The primary metric should be:

- **Causally proximate to the change being tested:** The metric should be directly affected by the variant, not downstream through a long and uncertain causal chain.
- **Sensitive enough to detect the MDE within the planned experiment duration:** A metric with very low variance or very low baseline rate may require impractically large sample sizes.
- **Aligned with the experiment hypothesis:** The primary metric operationalises the specific claim the experiment is testing. If the hypothesis is "this change will improve checkout completion," the primary metric is checkout conversion rate — not revenue per user, which is affected by order value, not just completion.
- **Stable in the control group:** A metric that is highly volatile in the control group will produce wide CIs and reduce power. Verify baseline stability before selecting.

### One Primary Metric Per Experiment

The constraint of one primary metric is not arbitrary — it is the mechanism that controls the family-wise error rate at the experiment level. With one pre-registered primary metric, the false positive rate is controlled at α = 0.05. With two co-primary metrics, the FWER rises to approximately 9.8%. With five, it reaches 22.6%. See the P-Hacking and Multiple Comparisons document for the full inflation table.

If two metrics are genuinely co-equal in importance, the correct design is either to apply a Bonferroni correction across both (adjusted α = 0.025 per metric) or to run two separate experiments, each powered against its own primary metric.

### What Primary Metric Results Mean

| Primary Metric Result | Decision Implication |
|---|---|
| Significant positive (p < 0.05, effect > MDE) | Necessary condition for Ship — check guardrails before confirming |
| Significant positive (p < 0.05, effect < MDE) | Kill — statistically significant but practically meaningless |
| Not significant, adequately powered | Kill — confirmed null, true effect likely below MDE |
| Not significant, underpowered | Extend — inconclusive, insufficient evidence |
| Significant negative | Kill — confirmed regression on primary |

---

## Secondary Metrics

### Purpose

Secondary metrics serve three functions in experiment analysis:

**Mechanistic confirmation:** They explain *why* the primary metric moved. A checkout conversion experiment that shows a significant primary lift should also show a corresponding lift in "add to cart" rate if the mechanism is working as hypothesised. A primary lift without supporting secondary movement warrants investigation — the effect may be real but driven by an unexpected mechanism.

**Directional context:** They provide signal about broader impact areas that are not captured by the primary metric alone. A primary metric of checkout conversion may be accompanied by secondary metrics on session duration, pages per session, and return visit rate — not as decision criteria, but as context for understanding the full user experience impact.

**Hypothesis generation:** Secondary metrics that reach significance when the primary does not are the raw material for future experiments. They suggest where effects may exist and what future primary metrics to target — but they do not validate the current experiment.

### What Secondary Metrics Are Not

- A fallback primary metric when the primary fails
- Independent grounds for a Ship decision
- Evidence that the experiment "worked" when the primary result is null

A result summary that leads with a significant secondary metric when the primary metric is not significant is a red flag for post-hoc metric substitution. The LLM should flag this pattern and apply the pre-registration rules from the P-Hacking document.

---

## Guardrail Metrics

### Purpose and Selection

Guardrail metrics protect against the most consequential failure modes of experimentation: shipping a variant that improves one metric by degrading another. They are chosen to represent the dimensions of product health that must be preserved regardless of what the primary metric shows.

Common guardrail metric categories:

**Revenue integrity:** Revenue per user, average order value, revenue per session. Protects against variants that inflate conversion rate by lowering the friction on low-value transactions, or that drive volume at the cost of margin.

**Engagement continuity:** Session depth, return visit rate, days active, feature usage breadth. Protects against variants that produce a short-term engagement spike (potentially novelty-driven) at the cost of long-term retention.

**User experience baselines:** Page load time, error rate, crash rate, support contact rate. Protects against variants that improve a product metric by degrading the technical experience. These are particularly important for back-end and infrastructure changes where user-facing metrics may lag.

**Core business metrics:** For experiments on sub-metrics (e.g., a feature-level engagement metric as primary), the core business metric (e.g., overall revenue) should be a guardrail to confirm that optimising the sub-metric does not cannibalise the whole.

### Guardrail Thresholds

Guardrail metrics require pre-specified regression thresholds — the level of negative movement that constitutes a violation. Two threshold types:

**Statistical threshold:** A guardrail is violated when the regression is statistically significant at a defined α level. Conventionally α = 0.05 (two-tailed), but high-sensitivity guardrails (e.g., revenue per user) may use α = 0.10 to reduce the risk of missing a real regression.

**Practical threshold:** A guardrail is violated when the point estimate or CI lower bound crosses a defined absolute threshold, regardless of significance. For example: "Revenue per user must not decline by more than 0.5% in absolute terms." This threshold catches economically meaningful regressions that may not reach statistical significance in shorter experiments.

Both threshold types should be pre-registered. A guardrail that has no defined threshold cannot be evaluated objectively at analysis time.

---

## When a Test Passes on Primary but Fails on Guardrail

This is the most operationally consequential scenario in the metric hierarchy — and the one most likely to produce an incorrect Ship decision in the absence of a structured framework.

### Why It Happens

A variant can simultaneously improve the primary metric and degrade a guardrail metric when:

- The change creates a trade-off in user behaviour (e.g., faster checkout completion at the cost of reduced cart value)
- The primary metric improvement is driven by a segment that the guardrail is not sensitive to
- The variant optimises locally (a specific funnel step) while degrading the broader experience
- The novelty effect inflates the primary metric while the guardrail captures longer-term behaviour less susceptible to novelty

### The Decision Rule

**A significant regression on any guardrail metric blocks the Ship decision, regardless of primary metric performance.**

This rule is unconditional. The following framings are not exceptions:

- "The revenue regression is small relative to the conversion lift." — The guardrail threshold exists precisely to define what "small" means. If the regression exceeds the threshold, the Ship is blocked.
- "The guardrail regression is borderline (p = 0.06)." — A borderline guardrail regression is not a clean pass. It is a signal to Extend or Escalate, not to Ship.
- "The primary metric lift outweighs the guardrail cost on a net basis." — Net impact calculations are a business judgment that requires human review. An automated system should Escalate, not resolve this trade-off autonomously.
- "The guardrail metric is less important than the primary." — Importance is captured in the metric hierarchy at design time. If a metric is in the guardrail tier, its regression is a blocking condition by definition.

### The Decision Paths

**Significant primary positive + significant guardrail regression:**
Kill or Escalate. Do not Ship. If the guardrail regression is large and clearly harmful, Kill. If the trade-off is complex or the business context suggests the primary lift may outweigh the guardrail cost, Escalate to human review with a full quantification of both effects.

**Significant primary positive + borderline guardrail regression (p 0.05–0.15):**
Escalate. The guardrail has not been formally violated but the signal is not clean. Extending to accumulate more guardrail evidence is appropriate if time allows. Do not Ship on an ambiguous guardrail.

**Significant primary positive + directionally negative but non-significant guardrail:**
Proceed with caution. Document the directional signal. If the guardrail metric has a practical threshold defined, check the point estimate and CI against it. If the CI lower bound approaches the practical threshold, Escalate. If the signal is clearly noise-level, the Ship may proceed with monitoring in place.

**Significant primary positive + clean guardrails:**
Ship, subject to all other validity checks passing.

---

## Metric Hierarchy in Practice: Common Structural Errors

**No guardrail metrics defined:**
The experiment has no protection against regressions on dimensions not captured by the primary metric. Any Ship decision is incomplete — the variant may be improving the primary at the cost of unmeasured harm. Guardrail metrics must be defined before launch.

**Too many guardrail metrics:**
If every tracked metric is a guardrail, the probability of at least one spurious violation increases with experiment count — eventually blocking all Ship decisions. Guardrail metrics should be limited to the three to five metrics that represent genuine existential risks to the product or business. Secondary metrics carry the remaining tracking load.

**Guardrail metrics without defined thresholds:**
A guardrail without a regression threshold cannot be evaluated at analysis time. "Revenue per user should not go down" is not an operational specification. "Revenue per user must not show a statistically significant decline at α = 0.05, or an absolute decline exceeding 0.5%" is.

**Using the primary metric as its own guardrail:**
The primary metric is the target of optimisation — it cannot simultaneously serve as a protection mechanism. Guardrail metrics must be orthogonal to or downstream of the primary.

---

## Metric Hierarchy Specification: Pre-Launch Requirements

The following must be documented before the experiment launches:

| Metric Tier | Required Documentation |
|---|---|
| Primary metric | Name, definition, baseline rate, MDE, test type |
| Secondary metrics | Names, definitions, interpretive role (mechanistic / contextual / hypothesis) |
| Guardrail metrics | Names, definitions, statistical threshold (α level), practical threshold (absolute bound) |

Any experiment reaching analysis without this documentation should be flagged. Metric assignments made after observing results are post-hoc and invalid — they convert confirmatory analysis into exploratory analysis and remove the protections the hierarchy was designed to provide.
