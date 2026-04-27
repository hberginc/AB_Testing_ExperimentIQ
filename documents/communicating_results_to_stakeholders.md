# Communicating Experiment Results to Stakeholders

## Purpose

Statistical outputs — p-values, confidence intervals, power estimates — are the inputs to a decision, not the decision itself. When communicating experiment results to non-technical stakeholders, the primary obligation is to translate those outputs into language that supports a clear, accurate, and actionable conclusion. Precision must be preserved; jargon must not be the vehicle for it.

This document defines how to frame results for non-technical audiences across three communication contexts: clear results that support a definitive recommendation, borderline results that do not, and negative results that require careful framing to prevent misinterpretation.

---

## The Core Communication Principle: Lead with the Recommendation

For most stakeholder communications, the recommendation comes first and the evidence follows. This is the inverse of how statistical analysis is structured — but it is the structure that serves decision-makers.

**Why this order works:**

Stakeholders need to know what to do before they can evaluate the evidence for doing it. Leading with numbers — "the p-value was 0.03 and the confidence interval was [+0.4pp, +2.0pp]" — requires the reader to interpret the statistics before they know what question the statistics are answering. Leading with the recommendation — "we recommend shipping the variant" — orients the reader and makes the evidence that follows legible.

The exception is when the result is inconclusive or when the recommendation is against stakeholder expectations. In these cases, the evidence should be laid out first to demonstrate that the conclusion is data-driven before the recommendation is stated. Delivering an unexpected recommendation without evidence leads to the evidence being discounted.

**Standard structure for a clear result:**

1. **Recommendation** — one sentence: ship, kill, or extend, and why in plain terms
2. **What the experiment tested** — one to two sentences on the hypothesis and change
3. **What the data showed** — effect size and direction in plain language, without statistical notation
4. **Confidence in the result** — a plain-language statement of how reliable the finding is
5. **Next steps** — what happens now, and who owns it

---

## Translating Statistical Concepts into Plain Language

### P-Values

P-values should not appear in stakeholder communications without translation. The raw number carries no intuitive meaning for a non-technical audience and frequently produces misinterpretation — either false certainty ("it's 97% likely to be true") or false dismissal ("it's just statistics").

**Translations by result type:**

| Statistical Result | Plain Language |
|---|---|
| p = 0.002 (highly significant) | "We are highly confident this result is not due to chance. The signal is strong and consistent." |
| p = 0.03 (significant) | "The result clears the standard confidence threshold. We have sufficient evidence to act." |
| p = 0.048 (borderline significant) | "The result just clears the threshold, but with limited margin. We have enough evidence to proceed, though the finding is not robust." |
| p = 0.08 (not significant) | "The data did not produce sufficient evidence of a real effect. This does not mean the variant failed — it means we cannot distinguish its effect from chance at this sample size." |
| p = 0.45 (clearly not significant) | "The experiment found no meaningful difference between the variant and control. The evidence points to no real effect." |

### Confidence Intervals

Confidence intervals can be communicated as a range of plausible outcomes without introducing the frequentist definition.

**Template:** "The data suggest the true improvement is likely between [lower bound] and [upper bound]. Our best single estimate is [point estimate], but the actual long-run effect could be anywhere in that range."

For wide intervals: "The result is directionally positive, but we have limited precision on the exact size of the effect. The true improvement could be as small as [lower bound] or as large as [upper bound]."

For intervals that include zero: "The range of plausible effects includes the possibility of no improvement — or even a slight decline. This is why we cannot make a confident recommendation based on this result alone."

### Statistical Power

Power does not need to be communicated as a number. The concept that matters to stakeholders is whether the experiment was designed to detect the effect size they care about.

**For adequate power:** "The experiment was sized to reliably detect improvements of [MDE] or larger. A non-significant result means the variant is unlikely to produce an improvement that large."

**For underpowered experiments:** "The experiment did not run long enough to reliably detect the improvement threshold we care about. A non-significant result here is inconclusive — not a confirmed finding that the variant doesn't work."

### Effect Size

Always lead with the absolute effect, then provide commercial context. Relative lift can follow as a secondary frame.

**Template:** "The variant improved conversion rate by [X] percentage points — from [baseline]% to [variant]%. At our current traffic volume, that translates to approximately [N] additional [conversions/customers/revenue events] per [time period], equivalent to roughly [£/$ value]."

Avoid: "The variant produced a statistically significant 12% relative improvement in conversion rate." — The relative figure without absolute context obscures whether the improvement is meaningful.

---

## Language for Clear Results

### Recommending Ship

> "Based on the experiment results, we recommend shipping the variant.
>
> The test ran for [duration] and showed that [variant description] increased [primary metric] from [X]% to [Y]% — an improvement of [Z] percentage points. At current traffic volume, this corresponds to approximately [commercial impact].
>
> The result clears our confidence threshold and the effect is large enough to be commercially meaningful. Guardrail metrics — including [revenue metric] and [engagement metric] — showed no significant decline.
>
> Recommended next step: ship to 100% of [target population] by [date]."

### Recommending Kill (Confirmed Null)

> "Based on the experiment results, we recommend closing this test without shipping the variant.
>
> The experiment was run with sufficient traffic to reliably detect an improvement of [MDE] or larger. The variant did not produce an improvement of that size — the data are consistent with the variant having little to no effect on [primary metric].
>
> This is a clean finding. The variant is unlikely to move the metric in a meaningful way. We recommend deprioritising this approach and [redirecting engineering effort / pursuing the alternative hypothesis from the secondary metrics]."

### Recommending Kill (Statistically Significant but Practically Meaningless)

This case requires the most careful framing. Stakeholders will see "statistically significant" and expect a Ship recommendation. The communication must explain why significance is not sufficient without undermining confidence in the experimentation programme.

> "The experiment produced a statistically significant result — meaning the improvement we measured is real and not due to chance. However, the size of the improvement is smaller than the threshold we set for this change to be worth shipping.
>
> The variant improved [primary metric] by [X] percentage points. At current volume, that corresponds to approximately [commercial impact] — below the [£/$] threshold we defined as the minimum to justify the engineering and opportunity cost of this change.
>
> We recommend closing the test without shipping. This is not a failed experiment — it is a precise finding that the improvement exists but is too small to act on. The variant is unlikely to become more impactful at larger scale."

---

## Language for Borderline and Inconclusive Results

Borderline results are the most difficult to communicate because the honest answer — "we don't know yet" — is frequently received as a failure of the experimentation process rather than a valid outcome of rigorous analysis. The communication must normalise uncertainty as a feature of good science, not a failure of execution.

### When to Use "Inconclusive"

Use "inconclusive" when:
- The experiment was underpowered and the result is not significant
- The result is borderline significant (p between 0.04 and 0.07) with a CI lower bound near zero
- Primary and secondary metrics are in conflict
- A guardrail metric shows a directionally negative but non-significant trend

Do not use "inconclusive" as a soft Kill. If the experiment was adequately powered and the primary metric is not significant, the result is a confirmed null — not inconclusive. The distinction matters: an inconclusive result warrants an Extend decision; a confirmed null warrants a Kill.

### Framing an Inconclusive Result

> "The experiment did not produce a definitive result — we don't yet have enough evidence to make a confident recommendation either way.
>
> The variant showed a [directional description — e.g., 'small positive trend'] in [primary metric], but the result did not reach the confidence level required to distinguish a real effect from chance variation. This is most likely because [the experiment did not run long enough / the effect, if it exists, is smaller than we originally estimated].
>
> We recommend [extending the experiment for an additional [duration] / re-running with a larger traffic allocation] to produce a conclusive result. The decision on this variant will be revisited by [date]."

### Framing a Primary-Guardrail Conflict

> "The experiment produced a mixed result that requires further review before a decision can be made.
>
> On the positive side: [primary metric] improved by [X] percentage points, clearing our significance and commercial thresholds. On the concerning side: [guardrail metric] showed a [directional description] of [magnitude], which [did / did not] reach our significance threshold.
>
> We are not recommending shipping at this time. The potential improvement to [primary metric] is real, but we need to understand whether the [guardrail] trend represents a genuine trade-off before committing to a decision. [Next step: human review / additional analysis / extended monitoring]."

---

## Framing Negative Results Constructively

Negative results — confirmed nulls and confirmed regressions — are often the most valuable outputs of an experimentation programme. A confirmed null eliminates a hypothesis that would otherwise consume future investment. A confirmed regression prevents harm. Both deserve constructive framing, not apologetic hedging.

**For confirmed nulls:**
> "The experiment gave us a clear answer: this approach does not produce a meaningful improvement in [metric]. That is a valuable finding — it rules out [approach] as a lever for [goal] and allows us to redirect effort toward [alternative]. We now know more precisely where the opportunity is not."

**For confirmed regressions:**
> "The experiment identified a real problem with the variant: [guardrail metric] declined significantly. Shipping this change would have [estimated harm]. The experiment did exactly what it was designed to do — it caught a regression before it reached users at scale."

Avoid framing negative results as failures. An experiment that prevents a bad ship is as valuable as one that enables a good ship. Communicate both types of outcome with the same level of confidence and specificity.

---

## Common Communication Anti-Patterns

- **Leading with the p-value:** Raw p-values in stakeholder communications produce misinterpretation and shift the conversation toward statistical debate rather than decision-making. Translate first; present the number only if asked.
- **Using "confidence" to mean p-value:** "We are 97% confident in this result" is not what a p-value of 0.03 means, and stating it this way will produce incorrect expectations about replicability and effect size certainty.
- **Hedging a clear result:** When the evidence supports a definitive recommendation, make it. Framing a clean Ship result with excessive caveats — "the data suggests we might consider potentially shipping" — creates ambiguity where none exists and invites stakeholders to second-guess a valid conclusion.
- **Softening a Kill recommendation:** A Kill based on a confirmed null or a practically meaningless result should be stated clearly. Framing it as "we may want to revisit this approach" or "the results were somewhat mixed" misrepresents the finding and leaves open a decision that the data has already closed.
- **Presenting relative lift without absolute context:** A "20% improvement" that corresponds to a 0.02 percentage point absolute lift will produce a Ship recommendation based on a misleading frame. Always anchor relative figures with the absolute effect and commercial translation.
- **Treating an inconclusive result as a soft Kill:** An underpowered inconclusive result is not evidence against the variant. Communicating it as "the experiment didn't show an improvement" implies a confirmed null when the data is silent on the question.
