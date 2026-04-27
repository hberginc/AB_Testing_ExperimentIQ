# Ship / Kill / Extend Decision Framework

## Purpose

Statistical significance is a necessary but insufficient condition for a ship decision. This document defines the reasoning framework for translating experiment results — including statistical outputs, business context, and risk factors — into one of three decisions: **Ship**, **Kill**, or **Extend**. Each decision has explicit criteria. Results that do not cleanly meet the criteria for Ship or Kill should default to Extend or escalate for manual review.

---

## The Three Decisions Defined

**Ship:** Deploy the variant to 100% of the target population. Requires confidence that the effect is real, directionally positive on the primary metric, not harmful to guardrail metrics, and large enough to be commercially meaningful.

**Kill:** Abandon the variant. Applies when the result is a confirmed null, a confirmed regression, or when the variant is statistically significant but the effect is too small to justify the cost of shipping.

**Extend:** Continue the experiment by collecting more data. Applies when the result is inconclusive due to insufficient power, borderline significance, or conflicting signals across metrics. Extend is not a neutral holding pattern — it is a deliberate decision to reduce uncertainty before acting.

---

## Primary Decision Criteria

### Ship When:
- The primary metric shows a statistically significant positive effect (p < 0.05, two-tailed by default)
- The CI lower bound clears the pre-defined MDE or commercial threshold — not just the point estimate
- No guardrail metric shows a statistically significant regression
- The experiment ran to its pre-registered sample size (was not stopped early)
- The test was adequately powered (power ≥ 0.80 at design time)
- The effect is consistent across key segments — a result driven entirely by one segment warrants investigation before shipping

### Kill When:
- The primary metric shows a statistically significant negative effect
- The experiment was adequately powered and the result is not significant — strong evidence the true effect is smaller than the MDE
- The result is statistically significant but the effect size falls below the commercial threshold (see: statistically significant but practically meaningless, below)
- A guardrail metric shows a significant regression, regardless of primary metric performance
- The variant cannot be shipped due to technical, legal, or product constraints discovered during the experiment

### Extend When:
- The experiment is underpowered and the result is not significant — inconclusive, not a confirmed null
- The result is borderline significant (p between 0.04 and 0.07) and the CI lower bound does not clearly clear the MDE
- Significant effects appear in secondary metrics but not the primary — directional signal exists but primary evidence is insufficient
- A guardrail metric shows a non-significant but directionally negative trend that warrants monitoring
- The experiment experienced a data quality issue (e.g., SRM — sample ratio mismatch) that invalidates the current result

---

## Statistically Significant but Practically Meaningless

This is one of the most consequential failure modes in high-traffic experimentation. It occurs when a large sample size produces a statistically significant result for an effect that has no commercial value.

**The pattern:** p < 0.05 (often p << 0.01), wide traffic volume, point estimate and CI both positive but the entire interval falls below the minimum commercially meaningful threshold.

**Example:** An experiment on 4 million users detects a conversion rate lift of 0.03 percentage points (95% CI: [+0.01pp, +0.05pp], p = 0.001). The result is highly significant. The estimated annual revenue impact at current volume is negligible relative to engineering and opportunity cost.

**The correct decision is Kill, not Ship.** Statistical significance establishes that the effect is real; it does not establish that the effect matters. The decision framework must apply a commercial threshold — ideally the MDE defined at experiment design — as a second gate after statistical significance.

**How to identify this scenario:**
- The CI upper bound is below the MDE defined at experiment design
- The point estimate, even if taken at face value, does not justify the cost of shipping
- The p-value is very small (p < 0.01) combined with a very large sample — a signal that power is inflating significance for trivial effects

**The risk of shipping anyway:** Shipping commercially meaningless changes consumes engineering capacity, adds code complexity, and creates a false precedent that statistical significance alone justifies a ship decision. In an automated system, this is a critical failure mode to gate against explicitly.

---

## Borderline Cases

Borderline results are those where no single decision is clearly correct. The appropriate response is to escalate for human review rather than resolve algorithmically. The following patterns define borderline territory:

**Borderline significance:**
p is between 0.04 and 0.07 and the CI lower bound is near zero. The result may be real or may be noise — the experiment has not produced sufficient evidence to distinguish between them. Default to Extend if traffic and time allow; escalate if not.

**CI lower bound at or near the MDE threshold:**
The point estimate clears the commercial threshold but the lower bound does not. The worst-case plausible effect may not justify shipping. Review the business context: is the decision reversible? What is the cost of a false positive vs. a false negative here?

**Conflicting primary and secondary metrics:**
The primary metric is significantly positive but one or more secondary metrics are significantly negative or show meaningful negative trends. This is not a clean Ship — the variant may be improving one dimension at the cost of another. Requires human interpretation of which metrics take precedence.

**Significant primary, borderline guardrail:**
The primary metric is clearly significant and positive, but a guardrail metric shows a negative trend that does not reach significance (p between 0.06 and 0.15). The guardrail has not been violated but the signal is not clean. Escalate rather than ship automatically.

**Winner's curse on a low-power significant result:**
The experiment was underpowered and the result reached significance. The point estimate is likely inflated. Apply a conservative discount to the effect size estimate and re-evaluate against the commercial threshold. If the discounted estimate no longer clears the MDE, treat as borderline and escalate.

---

## Business Context Factors

Statistical outputs alone do not determine the correct decision. The following business context factors must be incorporated before finalising a Ship or Kill recommendation:

**Reversibility:** Can the change be rolled back quickly if post-ship monitoring reveals a problem? Highly reversible changes (feature flags, UI copy) tolerate a lower evidence bar. Irreversible or difficult-to-reverse changes (data schema changes, pricing changes, infrastructure migrations) require a higher bar — consider requiring p < 0.01 and power ≥ 0.90.

**Strategic alignment:** Does the direction of the effect align with current product strategy? A statistically significant improvement in a metric that is being deprecated or deprioritised may not warrant shipping resources.

**Opportunity cost:** What is the cost of not shipping? If the variant addresses a known problem with high business priority, the cost of a false negative (Kill when should Ship) may outweigh the cost of a false positive. This does not lower the statistical bar — it is an input to the escalation decision.

**Interaction risk:** Does the variant interact with other live experiments or recent launches? If the test was run during a period of concurrent experimentation, the measured effect may be confounded. Flag for review if the experiment period overlaps with major product changes.

**Segment consistency:** A result that is significant in aggregate but driven entirely by one user segment (e.g., mobile only, new users only) may not generalise to the full population. Segment-driven results should be investigated before a full ship decision.

---

## Decision Table

| Statistical Result | Effect Size vs. MDE | Guardrail Status | Decision |
|---|---|---|---|
| Significant positive | Above MDE | Clean | Ship |
| Significant positive | Above MDE | Regression | Kill / Escalate |
| Significant positive | Below MDE | Clean | Kill (practically meaningless) |
| Significant negative | Any | Any | Kill |
| Not significant, adequately powered | Below MDE | Clean | Kill (confirmed null) |
| Not significant, underpowered | Unknown | Clean | Extend |
| Borderline significant (p 0.04–0.07) | Near MDE | Clean | Extend / Escalate |
| Significant positive | Above MDE | Borderline negative | Escalate |
| Significant, low-power design | Likely inflated | Clean | Escalate (winner's curse) |

---

## Anti-Patterns

- **Shipping on p-value alone without checking effect size against MDE:** The most common failure mode in automated systems. Statistical significance is a threshold for credibility, not a ship signal.
- **Killing on a non-significant result from an underpowered experiment:** A non-significant result from an underpowered experiment is not a confirmed null. Killing here discards potentially valid improvements.
- **Extending indefinitely to avoid a decision:** Extend is a deliberate decision to reduce uncertainty, not a mechanism for deferring a result that is uncomfortable. Every Extend decision should have a defined additional sample size or time horizon attached to it.
- **Overriding a Kill decision because the team has high conviction:** Business conviction is an input to experiment design (it determines the MDE), not an override of a completed experiment result. High conviction that is not reflected in the data is a signal to investigate methodology, not to ship.
- **Treating guardrail metric non-significance as guardrail clearance:** A guardrail metric that is directionally negative but not significant has not been cleared — it has not been violated at the current sample size. A borderline negative guardrail is a reason to Extend or Escalate, not to Ship.

---

## When to Escalate Rather Than Decide

Escalate to human review rather than producing an automated Ship / Kill / Extend recommendation when:

- Two or more of the borderline conditions above apply simultaneously
- The primary and a guardrail metric are in direct conflict
- The experiment result is being used to make an irreversible or high-stakes decision
- The statistical output and the business context point to different decisions
- The experiment validity cannot be confirmed (SRM, early stopping, data pipeline issues)
