"""Bulk/cut rate-of-change targets, with the lean:fat partition trade-off explicit.

Turns the "gain/lose ~0.25-0.5% bodyweight/week" prose already used
elsewhere in this library into a computed weekly-gain target in kg, banded
by trainee status, with the partition research shown as an explicit
trade-off rather than a single number that hides the trade-off.

Evidence grade: emerging. Garthe (2013) is a single well-designed controlled
trial with a modest n in an elite-athlete population (not general lifters);
Rozenek (2002) is older, smaller, and only directionally supportive; Helms's
specific thresholds are expert-synthesis (tier 4), not one dated study. This
is presented as a RANGE with the trade-off explicit, not a single "correct"
number - see the citations below for what's actually been measured vs.
extrapolated.

Sources:
    Garthe, I., Raastad, T., Refsnes, P.E., Sundgot-Borgen, J. (2013).
        Effect of nutritional intervention on body composition and
        performance in elite athletes. European Journal of Sport Science,
        13(3), 295-303. PMID 23679146. Two supervised bulking groups: a
        slower ~0.16%/week condition (the paper's ALG group) gained ~1.2 kg
        lean : ~0.2 kg fat (~86% lean by mass); a faster ~0.38%/week
        condition (the paper's NCG group) gained ~1.7 kg lean : ~1.1 kg fat
        (~61% lean by mass) - slower bulks partitioned leaner. These
        group-mean kg changes are derived from Garthe 2013's reported
        tables per two independent secondary reviews (Iraki et al., 2019,
        Sports, 7(7), 154; MacroFactor's published analysis of the same
        trial), since the primary table itself is paywalled and wasn't
        independently re-verified against the original PDF here. Small n,
        high variance - read the partition split as directional (slower =
        leaner), not a precise percentage.
    Rozenek, R. et al. (2002). Effects of high-calorie supplements on body
        composition and muscular strength following resistance training.
        Journal of Sports Medicine and Physical Fitness. Comparing surplus
        sizes in resistance-trained men: a larger surplus (~2000 kcal/day)
        added more total mass but a materially higher fat fraction - extra
        calories didn't convert proportionally to muscle. Directional
        finding, not a fitted coefficient - the exact percentages are
        study-specific.
    Helms, E. (practitioner synthesis, not a single dated RCT). ~0.25%/week
        for more advanced lifters is a reasonable target; ~0.5-1%/week is
        reasonable for novices. Aggressive bulk-then-cut cycles tend to net
        a 20-30% loss of the lean mass gained versus a slower rate that
        keeps more of it.
"""

from __future__ import annotations

from dataclasses import dataclass

# (low_pct, high_pct) weekly bodyweight % change, by self-reported trainee tier.
# Helms's practitioner synthesis - tier 4, not a single dated RCT (see docstring).
BULK_RATE_PCT_BY_TIER = {
    "novice": (0.5, 1.0),
    "intermediate": (0.25, 0.5),
    "advanced": (0.0, 0.25),
}

CUT_RATE_PCT_BY_TIER = {
    "novice": (0.5, 1.0),
    "intermediate": (0.5, 1.0),
    "advanced": (0.25, 0.75),
}

TIERS = tuple(BULK_RATE_PCT_BY_TIER)

# Garthe (2013) bulk-phase partition anchors: (rate_pct_per_week, lean_fraction, fat_fraction).
# Derived from the paper's reported group-mean kg changes (see module docstring):
# NCG (fast, ~0.38%/wk) +1.7kg lean / +1.1kg fat = 60.7/39.3, rounded to 61/39.
# ALG (slow, ~0.16%/wk) +1.2kg lean / +0.2kg fat = 85.7/14.3, rounded to 85/15.
# Directional, not precise - small n, high variance, secondary-source-derived.
GARTHE_2013_FAST_BULK = {"rate_pct_per_week": 0.38, "lean_fraction": 0.61, "fat_fraction": 0.39}
GARTHE_2013_SLOW_BULK = {"rate_pct_per_week": 0.16, "lean_fraction": 0.85, "fat_fraction": 0.15}


@dataclass
class RateTarget:
    """Weekly bodyweight-change target for a bulk or cut, with a partition note."""

    bodyweight_kg: float
    goal: str
    tier: str
    rate_low_pct: float
    rate_high_pct: float
    weekly_change_low_kg: float
    weekly_change_high_kg: float
    partition_note: str


def rate_target(bodyweight_kg: float, goal: str, tier: str = "intermediate") -> RateTarget:
    """Weekly weight-change target (kg) for a bulk or cut, banded by trainee tier.

    Args:
        bodyweight_kg: current bodyweight, kilograms.
        goal: "gain" (bulk) or "cut".
        tier: "novice", "intermediate", or "advanced" - controls the %BW/week
            band (see BULK_RATE_PCT_BY_TIER / CUT_RATE_PCT_BY_TIER).

    Raises:
        ValueError: if bodyweight_kg <= 0, goal isn't "gain"/"cut", or tier
            isn't a known tier.
    """
    if bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg must be > 0")
    if goal not in ("gain", "cut"):
        raise ValueError(f"goal must be 'gain' or 'cut', got {goal!r}")
    if tier not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}, got {tier!r}")

    table = BULK_RATE_PCT_BY_TIER if goal == "gain" else CUT_RATE_PCT_BY_TIER
    low_pct, high_pct = table[tier]

    if goal == "gain":
        note = (
            f"Garthe 2013: near {GARTHE_2013_SLOW_BULK['rate_pct_per_week']}%/wk partitioned roughly "
            f"{GARTHE_2013_SLOW_BULK['lean_fraction']*100:.0f}% lean; near "
            f"{GARTHE_2013_FAST_BULK['rate_pct_per_week']}%/wk partitioned roughly "
            f"{GARTHE_2013_FAST_BULK['lean_fraction']*100:.0f}% lean - slower bulks partition leaner. "
            "Derived from the paper's reported group-mean kg changes per two independent reviews "
            "of its tables (primary table is paywalled, not independently re-verified here) - "
            "small n, high variance: directional, not precise."
        )
    else:
        note = (
            "Faster cuts risk more lean-mass loss; keep protein high and training hard. "
            "Helms: aggressive bulk-then-cut cycles tend to net a 20-30% loss of lean mass gained "
            "versus a slower, steadier rate."
        )

    return RateTarget(
        bodyweight_kg=bodyweight_kg,
        goal=goal,
        tier=tier,
        rate_low_pct=low_pct,
        rate_high_pct=high_pct,
        weekly_change_low_kg=bodyweight_kg * low_pct / 100.0,
        weekly_change_high_kg=bodyweight_kg * high_pct / 100.0,
        partition_note=note,
    )
