# Novelty Effect: Definition, Detection, and Decision Impact

## Definition

The **novelty effect** is a temporary inflation of a metric caused by user curiosity or behavioural change in response to something new, rather than by the intrinsic value of the change itself. When a variant introduces a visible or experiential difference, a new UI layout, a new feature, a changed flow, a subset of users will engage with it at an elevated rate simply because it is different. This elevated engagement decays as novelty wears off and behaviour returns to baseline.

The novelty effect is a **temporal confound**, not a measurement error. The experiment is measuring real behaviour, but the behaviour being measured is a transient response to newness, not a stable response to value. A result driven by novelty will not hold at scale or over time. Shipping on a novelty-inflated result produces a variant whose measured lift does not materialise in post-ship monitoring.

The inverse, the **familiarity effect** or **change aversion**, also exists: users briefly underperform on a new variant because the change disrupts habitual behaviour, then recover as they adapt. This produces a temporary suppression of the metric that can cause a genuinely good change to appear neutral or negative in the short term. Both directions must be accounted for in experiment duration planning and result interpretation.

---

## When Novelty Effect Is Most Likely

Not all experiments are equally susceptible. Novelty effect risk is highest when:

- **The variant is visually distinct:** Layout changes, redesigns, new navigation structures, or prominent new UI elements are high-risk. Users notice and explore.
- **The variant introduces a new feature:** First-time exposure to a feature drives engagement that will not be sustained once the feature is familiar.
- **The affected users are returning or habitual users:** Novelty effect requires prior familiarity with the control experience. New users have no baseline to be disrupted from, the effect is concentrated in returning user segments.
- **The metric is engagement-based:** Click rate, feature interaction, session depth, and time-on-page are more susceptible than conversion rate or revenue, which require user intent beyond curiosity.
- **The experiment runs for less than two weeks:** Short experiments may capture only the novelty peak without the subsequent decay.

Novelty effect is less likely when the variant change is invisible to the user (back-end, infrastructure, algorithm changes) or when the metric is a downstream conversion event with a long consideration cycle.

---

## Detection Heuristic: Week-1 vs. Week-2 Metric Comparison

The primary detection method for novelty effect is a **temporal cohort analysis** comparing metric performance in the first week of the experiment against the second week, within the variant group.

### The Logic

If the measured lift is driven by genuine value, it should be stable across time, users who encounter the variant in week 1 should show similar behaviour to users who encounter it in week 2, once the initial assignment period has passed. If the lift is driven by novelty, week-1 users will show elevated engagement that decays in week 2 as the novelty wears off.

### How to Run the Check

Split the variant's user population into two cohorts by assignment date:
- **Week-1 cohort:** Users assigned in the first 7 days of the experiment
- **Week-2 cohort:** Users assigned in days 8–14 of the experiment

Compute the primary metric separately for each cohort and compare. Apply the same comparison to the control group to establish a baseline, control metrics should be stable across cohorts by construction, since there is no novelty to decay.

| Cohort | Control Metric | Variant Metric | Lift |
|---|---|---|---|
| Week 1 | 4.1% | 5.2% | +1.1pp |
| Week 2 | 4.0% | 4.2% | +0.2pp |

In this example, the aggregate result would show a significant positive lift. The cohort breakdown reveals that the lift is concentrated in week 1 and has nearly disappeared by week 2, a strong novelty effect signal.

### Interpreting the Heuristic

- **Stable lift across cohorts:** No novelty effect signal. The measured lift is likely to persist post-ship.
- **Declining lift from week 1 to week 2:** Novelty effect is present. The aggregate result overstates the likely steady-state effect.
- **Increasing lift from week 1 to week 2:** Possible familiarity or learning effect, users improving with the variant over time. This is a positive signal and suggests the aggregate result may understate long-term value.
- **Negative week-1 lift recovering in week 2:** Change aversion followed by adaptation. The aggregate result may understate true value if the experiment ended before full adaptation.

### Limitations of the Heuristic

The week-1 vs. week-2 comparison has structural limitations that must be acknowledged:

- **Cohort size imbalance:** If traffic ramps up over the experiment period, week-2 cohorts may be larger than week-1 cohorts, making direct comparison noisy.
- **Seasonal or external confounds:** Differences between week 1 and week 2 may reflect external events (day-of-week effects, marketing activity, product changes) rather than novelty decay. Always check whether control cohorts are also stable before attributing week-over-week variance to novelty.
- **Two weeks may not be enough:** For low-frequency behaviours or products with long engagement cycles, novelty decay may extend beyond two weeks. The heuristic is a practical default, not a universal boundary.
- **New user contamination:** If the variant attracts a different mix of new vs. returning users across weeks, the cohort comparison may reflect composition differences rather than novelty decay. Segment by new vs. returning users to isolate the effect.

---

## How Novelty Effect Affects Ship / Kill Decisions

### When Novelty Effect Is Detected: Do Not Ship on the Aggregate Result

A statistically significant aggregate result that shows strong week-over-week decay in the variant should not be treated as a Ship signal. The measured lift does not represent steady-state behaviour and will not hold post-ship. Shipping on a novelty-inflated result produces a variant whose true long-run effect is the week-2 estimate, or lower, not the aggregate.

The correct decision path when novelty effect is detected:

1. **Use the week-2 estimate as the conservative effect size**, not the aggregate. Evaluate this estimate against the MDE and commercial threshold. If the week-2 estimate clears the threshold, the result may still support a Ship decision, the novelty-inflated week-1 data has not destroyed the finding, it has obscured it.
2. **If the week-2 estimate does not clear the threshold:** Extend the experiment to collect more stable data, or Kill if the week-2 estimate is clearly below the commercial threshold and the experiment was adequately powered.
3. **Do not average the week-1 and week-2 estimates** to produce a "corrected" aggregate. This understates the problem, the week-1 data is not slightly noisy, it is measuring a different behavioural state.

### When Change Aversion Is Detected: Do Not Kill on the Aggregate Result

A non-significant or negative aggregate result that shows improving lift from week 1 to week 2 should not be treated as a Kill signal. The variant may be genuinely valuable but measured during an adaptation period. Killing here discards a potentially valid improvement.

The correct decision path:

1. **Use the week-2 estimate as the signal**, not the aggregate. If the week-2 metric is moving in the right direction and approaching significance, Extend the experiment to allow adaptation to stabilise.
2. **Check whether the week-2 lift is approaching the MDE.** If it is, the experiment needs more time, not a Kill decision.
3. **Do not Extend indefinitely.** Set a defined additional duration (e.g., one additional week) and commit to a decision at that point regardless of the result.

### Interaction with Returning vs. New Users

Because novelty effect is concentrated in returning users, a useful secondary check is to split results by user type:

- **Returning users showing high lift, new users showing low lift:** Consistent with novelty effect in the returning segment. The new user result is a cleaner estimate of true value for that segment.
- **New users showing high lift, returning users showing low lift:** Consistent with change aversion in returning users, the new experience may be better for new users but disruptive for those with established habits.

Neither pattern alone is a Ship or Kill signal, but both inform which segment the variant is serving and whether the aggregate result is representative.

---

## Experiment Design Implications

The best response to novelty effect is to design experiments that are long enough to observe post-novelty behaviour before the analysis window closes.

**Minimum recommended duration:** Two full weeks for any experiment involving a visible UI or feature change affecting returning users. This allows at least one week of post-novelty data to be observed and the week-1 vs. week-2 heuristic to be applied.

**For high-novelty changes:** Consider a minimum of three to four weeks, or pre-register the analysis to use only the final week's data as the primary metric window, with the full experiment period used only for power accumulation.

**New user vs. returning user splits:** Pre-register segment-level analysis for experiments where novelty effect risk is high. This avoids the temptation to run the split post-hoc as a correction for a result that didn't meet expectations.

---

## Anti-Patterns

- **Shipping on a significant aggregate result without checking for week-over-week stability:** The most consequential novelty effect error. A significant aggregate result is not sufficient evidence of a durable effect when the variant is a visible change.
- **Killing on a non-significant aggregate result from a short experiment involving a visible change:** May be discarding a genuine improvement during the adaptation period. Duration and cohort analysis should precede a Kill decision in this scenario.
- **Running novelty-susceptible experiments for less than two weeks:** Insufficient duration to detect novelty decay or allow adaptation. The experiment will produce either an inflated positive or a suppressed result depending on which direction the transient effect runs.
- **Treating the week-1 vs. week-2 heuristic as definitive without checking control cohort stability:** External confounds can produce week-over-week differences in both control and variant. The heuristic is only valid when control cohorts are stable.
- **Applying novelty effect reasoning to back-end or invisible changes:** Novelty effect requires user awareness of the change. Flagging novelty risk on an algorithm or infrastructure change with no visible user impact is incorrect and will produce spurious escalations.

---

## Summary: Novelty Effect Decision Rules

| Signal | Indicated Decision |
|---|---|
| Stable lift week 1 → week 2, clears MDE | Ship |
| Declining lift week 1 → week 2, week-2 estimate clears MDE | Ship on week-2 estimate with caution |
| Declining lift week 1 → week 2, week-2 estimate below MDE | Kill or Extend for more stable data |
| Negative or neutral week 1, improving week 2 | Extend, change aversion, allow adaptation |
| Stable non-significant result, adequately powered | Kill (confirmed null, not novelty-driven) |
| High novelty risk, experiment < 2 weeks | Extend, insufficient duration to assess stability |
