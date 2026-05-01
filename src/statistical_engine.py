'''
 Statistical Engine

1. Ingest a CSV with control/variant metrics
2. Calculate p-values, confidence intervals, relative lift
3. Flag underpowered tests (sample size checks)
4. Output a structured result dictionary
'''

import pandas as pd
import numpy as np
import scipy.stats as stats
import math

def calculate_pvalue(
    control_visitors: int,
    variant_visitors: int,
    control_conversions: int,
    variant_conversions: int,
    test_tails: str = 'two_tailed',
    test_direction: str = 'superiority',
) -> float:
    """
    Two-proportion z-test with pooled variance.

    Parameters
    ----------
    control_visitors, variant_visitors   : sample sizes
    control_conversions, variant_conversions : successes
    test_tails      : 'one_tailed' | 'two_tailed'
    test_direction  : 'superiority' | 'non_inferiority'

    Returns
    -------
    float : p-value rounded to 4 decimal places
    """
    p_c = control_conversions / control_visitors
    p_v = variant_conversions / variant_visitors

    # Pooled proportion and standard error under H0
    p_pool = (control_conversions + variant_conversions) / (control_visitors + variant_visitors)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / control_visitors + 1 / variant_visitors))

    z_stat = (p_v - p_c) / se

    if test_tails == 'two_tailed':
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        # superiority and non_inferiority both test right tail (variant >= control)
        if test_direction in ('superiority', 'non_inferiority'):
            p_value = 1 - stats.norm.cdf(z_stat)
        else:
            p_value = stats.norm.cdf(z_stat)

    return round(p_value, 4)

def add_pvalues(df: pd.DataFrame) -> pd.DataFrame:
    """Apply calculate_pvalue() row-wise and add p_values + Significant_Results columns."""
    results = []
    for _, row in df.iterrows():
        res = calculate_pvalue(
            control_visitors=int(row['control_visitors']),
            variant_visitors=int(row['variant_visitors']),
            control_conversions=int(row['control_conversions']),
            variant_conversions=int(row['variant_conversions']),
            test_tails=row['test_tails'],
            test_direction=row['test_direction'],
        )
        results.append(res)

    out = df.copy()
    out['p_values'] = results
    out['Significant_Results'] = np.where(out['p_values'] < out['alpha'], 'Significant', 'Not-Significant')
    return out


def confidence_interval(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    alpha: float,
    test_tails: str = 'two_tailed',
) -> dict:
    """
    Confidence interval for the absolute lift (p_variant - p_control).

    Two-tailed → symmetric (ci_lower, ci_upper)
    One-tailed → lower bound only (ci_lower, ci_upper=None)

    Returns
    -------
    dict: absolute_lift, ci_lower, ci_upper, z_critical
    """
    p_c = control_conversions / control_visitors
    p_v = variant_conversions / variant_visitors
    lift = p_v - p_c

    # Unpooled SE — reflects actual variance, not H0 pooled estimate
    se = math.sqrt(
        p_c * (1 - p_c) / control_visitors +
        p_v * (1 - p_v) / variant_visitors
    )

    if test_tails == 'two_tailed':
        z = stats.norm.ppf(1 - alpha / 2)       # e.g. 1.96 at α=0.05
        ci_lower = round(lift - z * se, 6)
        ci_upper = round(lift + z * se, 6)
    else:
        z = stats.norm.ppf(1 - alpha)            # e.g. 1.645 at α=0.05
        ci_lower = round(lift - z * se, 6)       # one-sided lower bound
        ci_upper = None

    return {
        'absolute_lift': round(lift, 6),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'z_critical': round(z, 4),
    }

def required_sample_size(
    baseline_rate: float,
    mde_relative_pct: float,
    alpha: float,
    power: float = 0.80,
    tails: str = 'two_tailed',
) -> dict:
    """
    Calculate required sample size per variant using the two-proportion
    z-test power formula.

    Parameters
    ----------
    baseline_rate    : control conversion rate (e.g. 0.10 for 10%)
    mde_relative_pct : minimum detectable effect as relative % (e.g. 5.0 for 5%)
    alpha            : significance level (Type I error)
    power            : desired power = 1 − β (default 0.80)
    tails            : 'one_tailed' | 'two_tailed'

    Returns
    -------
    dict with sample sizes, rates, and z-scores
    """
    absolute_mde  = baseline_rate * (mde_relative_pct / 100)
    variant_rate  = baseline_rate + absolute_mde
    p_avg         = (baseline_rate + variant_rate) / 2

    # Critical z-scores
    z_alpha = stats.norm.ppf(1 - alpha) if tails == 'one_tailed' else stats.norm.ppf(1 - alpha / 2)
    z_beta  = stats.norm.ppf(power)

    # Two-proportion sample size formula
    numerator   = (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) +
                   z_beta  * math.sqrt(baseline_rate * (1 - baseline_rate) +
                                       variant_rate  * (1 - variant_rate))) ** 2
    denominator = absolute_mde ** 2
    n = math.ceil(numerator / denominator)

    return {
        'sample_size_per_variant': n,
        'total_sample_size': n * 2,
        'variant_rate_assumed': round(variant_rate, 6),
        'absolute_mde': round(absolute_mde, 6),
        'z_alpha': round(z_alpha, 4),
        'z_beta': round(z_beta, 4),
    }

def observed_power(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    alpha: float,
    test_tails: str = 'two_tailed',
) -> float:
    """
    Estimate the statistical power the test actually had, given real sample sizes.
    Uses the non-centrality approach: how many SEs the true effect sits above
    the critical threshold.

    Returns
    -------
    float : power between 0 and 1
    """
    p_c = control_conversions / control_visitors
    p_v = variant_conversions / variant_visitors
    absolute_lift = abs(p_v - p_c)

    # SE under alternative hypothesis (unpooled)
    se_alt = math.sqrt(
        p_c * (1 - p_c) / control_visitors +
        p_v * (1 - p_v) / variant_visitors
    )

    if se_alt == 0:
        return 0.0

    z_crit = stats.norm.ppf(1 - alpha / 2) if test_tails == 'two_tailed' else stats.norm.ppf(1 - alpha)

    # Non-centrality parameter: true effect in units of SE
    ncp   = absolute_lift / se_alt
    power = 1 - stats.norm.cdf(z_crit - ncp)

    return round(float(power), 4)


def flag_underpowered(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    baseline_rate: float,
    mde_relative_pct: float,
    alpha: float,
    test_tails: str,
    power_threshold: float = 0.80,
) -> dict:
    """
    Compare required vs actual sample sizes and compute observed power
    to determine if a test was underpowered.

    Returns
    -------
    dict with power diagnostics and underpowered flag
    """
    req = required_sample_size(baseline_rate, mde_relative_pct, alpha, power_threshold, test_tails)
    obs = observed_power(control_conversions, control_visitors,
                         variant_conversions, variant_visitors,
                         alpha, test_tails)

    actual_total   = control_visitors + variant_visitors
    required_total = req['total_sample_size']

    return {
        'observed_power':              obs,
        'required_sample_per_variant': req['sample_size_per_variant'],
        'required_sample_total':       required_total,
        'actual_sample_total':         actual_total,
        'sample_deficit':              max(0, required_total - actual_total),
        'is_underpowered':             obs < power_threshold,
        'power_threshold':             power_threshold,
    }

def analyze_experiment(row: pd.Series, power_threshold: float = 0.80) -> dict:
    """
    Full statistical analysis for a single A/B experiment row.

    Parameters
    ----------
    row             : a single row from the experiments DataFrame
    power_threshold : minimum acceptable power (default 0.80)

    Returns
    -------
    Structured dict — the output contract for Phase 3 LLM narrative.
    """
    c_conv = int(row['control_conversions'])
    c_vis  = int(row['control_visitors'])
    v_conv = int(row['variant_conversions'])
    v_vis  = int(row['variant_visitors'])

    p_val = calculate_pvalue(c_vis, v_vis, c_conv, v_conv,
                              row['test_tails'], row['test_direction'])

    ci    = confidence_interval(c_conv, c_vis, v_conv, v_vis,
                                row['alpha'], row['test_tails'])

    power = flag_underpowered(c_conv, c_vis, v_conv, v_vis,
                              row['control_conversion_rate'],
                              row['mde_relative_pct'],
                              row['alpha'], row['test_tails'],
                              power_threshold)

    is_sig = p_val < row['alpha']
    p_c    = row['control_conversion_rate']
    rel_lift = round((ci['absolute_lift'] / p_c) * 100, 2) if p_c > 0 else None

    return {
        # Identity
        'test_id':              row['test_id'],
        'test_name':            row['test_name'],
        'product_area':         row['product_area'],
        'hypothesis':           row['hypothesis'],
        'primary_metric':       row['primary_metric'],
        'audience_segment':     row['audience_segment'],
        'test_duration_days':   row['test_duration_days'],

        # Test design
        'test_tails':           row['test_tails'],
        'test_direction':       row['test_direction'],
        'alpha':                row['alpha'],
        'mde_relative_pct':     row['mde_relative_pct'],

        # Sample sizes
        'control_visitors':     c_vis,
        'variant_visitors':     v_vis,
        'control_conversions':  c_conv,
        'variant_conversions':  v_conv,

        # Core rates
        'control_rate':         round(row['control_conversion_rate'], 6),
        'variant_rate':         round(row['variant_conversion_rate'], 6),

        # Statistical output
        'p_value':              p_val,
        'is_significant':       is_sig,
        'absolute_lift':        ci['absolute_lift'],
        'relative_lift_pct':    rel_lift,
        'ci_lower':             ci['ci_lower'],
        'ci_upper':             ci['ci_upper'],

        # Power diagnostics
        'observed_power':              power['observed_power'],
        'is_underpowered':             power['is_underpowered'],
        'required_sample_per_variant': power['required_sample_per_variant'],
        'required_sample_total':       power['required_sample_total'],
        'actual_sample_total':         power['actual_sample_total'],
        'sample_deficit':              power['sample_deficit'],

        # Revenue context
        'revenue_delta':        row['revenue_delta'],
        'avg_order_value':      row['avg_order_value'],

        # Ground truth (for validation only — not fed to LLM)
        'outcome_type':         row['outcome_type'],
        'analyst':              row['analyst'],
    }