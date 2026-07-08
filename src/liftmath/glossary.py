"""Plain-English glossary: every piece of jargon liftmath uses, defined twice -
a beginner-friendly one-liner and the precise technical meaning.

This is the single Python-side source of truth for both the CLI's `glossary`
subcommand and the short inline asides `cli.py` prints the first time a term
shows up in a given command's output. The web app mirrors this same term
list and the same English wording by hand in `web/js/glossary.js` (the
language-neutral key list) and `web/js/i18n/en.js` (the `glossary.*`
strings) - the same discipline this project already uses to keep the JS math
pinned to the Python reference (see `onerm.py` / `web/js/math/one-rep-max.js`
for that pattern), applied to prose instead of formulas. There's no build
step to enforce this automatically for text the way `tools/gen_fixtures.py`
does for numbers, so a change here should be copied into `en.js` by hand in
the same commit.

Ordering is deliberate (roughly: 1RM axis, RIR/RPE axis, volume/mesocycle,
nutrition, body composition, relative-strength scoring, program templates,
symmetry, session load) so `liftmath glossary`'s full listing reads like a
guided tour instead of an alphabet-soup dump.

A couple of terms are deliberately NOT defined more precisely than the
evidence supports:
    - DOTS: what the letters stand for is disputed across sources that cite
      it, so this glossary describes what it DOES, not what it stands for.
    - IPF GL: the source material this project cites (see standards.py's
      module docstring) never expands "GL" either, so this glossary follows
      that same caution rather than asserting an unverified expansion.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    """One glossary entry: display name, a beginner one-liner, and the technical meaning."""

    term: str
    plain: str
    technical: str


# key -> Term. Insertion order is the display order for `liftmath glossary`
# (see module docstring) - keep web/js/glossary.js's GLOSSARY_TERMS array in
# this same order.
GLOSSARY: dict[str, Term] = {
    "1rm": Term(
        "1RM",
        "The most weight you could lift one time with good form.",
        "One-repetition maximum: the maximal load for a single successful rep of a given lift.",
    ),
    "e1rm": Term(
        "e1RM",
        "An estimated 1RM, worked out from a lighter set instead of an actual max-effort single.",
        "Estimated one-rep max: computed from a submaximal set (weight x reps) via a rep-max "
        "formula rather than measured directly.",
    ),
    "consensus": Term(
        "consensus",
        "This app's e1RM isn't one formula's guess - it's the median of six formulas, so one "
        "outlier equation can't skew the number.",
        "The median value across the applicable rep-max formulas for a given set, reported "
        "instead of any single formula's output.",
    ),
    "rir": Term(
        "RIR",
        "Reps in reserve - how many more reps you could have done before hitting failure.",
        "Reps In Reserve: the gap between reps performed and true momentary failure for a set.",
    ),
    "rpe": Term(
        "RPE",
        "Rate of perceived exertion - a 0-10 gut check on how hard a set felt, where 10 is failure.",
        "Rating of Perceived Exertion (Borg CR-10-style, resistance-training adaptation): a 0-10 "
        "exertion scale where RPE = 10 minus RIR.",
    ),
    "amrap": Term(
        "AMRAP",
        "As many reps as possible - a set you push to failure (or close to it) instead of "
        "stopping at a fixed rep count.",
        "As Many Reps (or Rounds) As Possible: an open-ended set taken to concentric failure or "
        "an agreed stopping point, used in 5/3/1 and nSuns to gauge progress.",
    ),
    "training_max": Term(
        "training max",
        "A number you train off that's a bit lighter than your true 1RM, so a program's "
        "percentages stay hittable week after week.",
        "A deliberately submaximal percentage of a tested (or estimated) 1RM - typically 90% - "
        "used as the base for percentage-based programming (Wendler's 5/3/1 convention).",
    ),
    "hard_set": Term(
        "hard set",
        "A set pushed close to failure - not a warm-up, not a set stopped way early.",
        "A working set taken to roughly 0-4 reps in reserve; the unit the volume landmarks "
        "(MV/MEV/MAV/MRV) are counted in.",
    ),
    "mv": Term(
        "MV",
        "Maintenance volume - the least weekly work that keeps a muscle from shrinking.",
        "Minimum weekly hard-set volume needed to maintain current muscle size without gaining.",
    ),
    "mev": Term(
        "MEV",
        "Minimum effective volume - the least weekly work that actually makes a muscle grow.",
        "The minimum weekly hard-set volume needed to produce a hypertrophy adaptation above "
        "maintenance.",
    ),
    "mav": Term(
        "MAV",
        "Maximum adaptive volume - the sweet-spot range where most of your growth happens.",
        "The weekly hard-set range producing the best rate of adaptation, before returns flatten "
        "or fatigue outpaces recovery.",
    ),
    "mrv": Term(
        "MRV",
        "Maximum recoverable volume - the most weekly work you can still recover from.",
        "The upper weekly hard-set ceiling beyond which fatigue accumulates faster than it can be "
        "recovered from.",
    ),
    "deload": Term(
        "deload",
        "A planned easy week - less weight and/or fewer sets - so fatigue can dissipate before it "
        "turns into a stall or an injury.",
        "A short block (typically one week) of reduced training volume and/or intensity, used to "
        "dissipate accumulated fatigue between mesocycles.",
    ),
    "mesocycle": Term(
        "mesocycle",
        "A training block, usually a few weeks long, that builds toward a peak and ends in a "
        "deload.",
        "A multi-week training block (commonly 4-8 weeks) organized around progressive overload, "
        "ending in a deload before the next block begins.",
    ),
    "recomp": Term(
        "recomp",
        "Building muscle and losing fat at the same time, by eating around maintenance calories "
        "instead of bulking or cutting.",
        "Body recomposition: training at maintenance (or a very small deficit) with high protein, "
        "aiming for simultaneous fat loss and muscle gain - realistically fastest for novices, "
        "returning trainees, or higher-body-fat individuals.",
    ),
    "partition": Term(
        "partition",
        "How a weight change splits between muscle and fat - a \"leaner\" bulk means more of the "
        "gain is muscle.",
        "The lean-mass-to-fat-mass ratio of a given weight change (e.g. a bulk's kg of lean "
        "tissue vs. kg of fat gained).",
    ),
    "t1t2t3": Term(
        "T1/T2/T3",
        "GZCLP's three tiers by how hard they're pushed: T1 is your heaviest main lift, T2 is a "
        "lighter secondary lift, T3 is an accessory pumped for volume.",
        "GZCL-method tiers by intensity/effort: T1 (main lift, near-maximal, low reps), T2 "
        "(secondary lift, moderate load/reps), T3 (accessory, higher reps, progressed by an AMRAP "
        "threshold).",
    ),
    "tdee": Term(
        "TDEE",
        "Total daily energy expenditure - roughly how many calories you burn in a day, which is "
        "also the number that keeps your weight stable if you eat exactly that much.",
        "Total Daily Energy Expenditure: estimated total calories burned per day (BMR plus "
        "activity), used as the maintenance-calorie anchor for a macro target.",
    ),
    "bmr": Term(
        "BMR",
        "Basal metabolic rate - the calories your body burns just to stay alive at rest, before "
        "any activity is added.",
        "Basal Metabolic Rate (most of the equations that estimate this actually measure/predict "
        "RMR, resting metabolic rate - a very close, slightly higher-condition cousin of true "
        "BMR): energy expenditure at rest, the base TDEE is built on top of.",
    ),
    "ffmi": Term(
        "FFMI",
        "Fat-free mass index - like BMI, but for muscle instead of total weight, so it's a rough "
        "gauge of how muscular someone is for their height.",
        "Fat-Free Mass Index: lean mass (kg) divided by height (m) squared, normalized to a "
        "1.80 m reference height (Kouri et al., 1995).",
    ),
    "navy_bf": Term(
        "Navy body-fat",
        "A body-fat estimate from a tape measure around your neck and waist (plus hips for "
        "women) - no calipers or scan needed.",
        "The U.S. Navy circumference method (Hodgdon & Beckett, 1984): body-fat % estimated from "
        "neck/waist(/hip) measurements and height via a logarithmic regression.",
    ),
    "cunningham": Term(
        "Cunningham",
        "A calorie-needs formula that uses your lean body mass instead of total bodyweight - "
        "built for people who are already lean and trained.",
        "Cunningham (1980): RMR = 500 + 22 x lean mass (kg); shown accurate specifically for "
        "athlete populations, less so for general (non-athlete) samples.",
    ),
    "mifflin": Term(
        "Mifflin",
        "The calorie-needs formula this app defaults to once it knows your age, height, and sex "
        "- the best general-purpose one in the research.",
        "Mifflin-St Jeor (1990): RMR from bodyweight, height, age, and sex; the equation with the "
        "best combination of accuracy and precision against measured RMR across general "
        "populations (Frankenfield et al., 2005).",
    ),
    "wilks": Term(
        "Wilks",
        "A score that lets you compare lifters of different bodyweights on one scale - a bigger "
        "number means a stronger relative total.",
        "A polynomial coefficient (fit per sex) multiplied by a competition total to produce a "
        "bodyweight-normalized score; the 2020 revision is this app's default, the original 1994 "
        "formula is kept for historical comparison.",
    ),
    "dots": Term(
        "DOTS",
        "Another bodyweight-normalized strength score, similar to Wilks but from a newer formula "
        "- what the letters stand for isn't agreed on, so this app doesn't guess.",
        "A 2019 bodyweight-normalization formula (quartic in bodyweight) adopted by USAPL/IPF as "
        "a Wilks alternative. The acronym's expansion is disputed across sources that cite it, so "
        "none is asserted here.",
    ),
    "ipf_gl": Term(
        "IPF GL",
        "The International Powerlifting Federation's own official scoring formula for comparing "
        "totals across bodyweights.",
        "IPF GL Coefficients for Relative Scoring (May 2020): coefficient = 100 / (A - B*e^(-C*"
        "bodyweight)), points = coefficient x total. Classic (raw) powerlifting only here.",
    ),
    "mcculloch": Term(
        "McCulloch",
        "An age adjustment applied on top of a bodyweight-normalized score, for comparing masters "
        "(40+) lifters against open-age standards.",
        "A multiplier (WRPF's published coefficient table, ages 40-90) applied to a total to "
        "age-adjust it for masters-category comparison - the same idea as Wilks/DOTS, but "
        "normalizing for age instead of bodyweight.",
    ),
    "531": Term(
        "5/3/1",
        "Jim Wendler's classic strength program: four-week waves building to a top single, named "
        "for the rep scheme of its final \"money\" week.",
        "A percentage-based periodization template (Wendler) run off a training max, cycling "
        "through 65/75/85%, 70/80/90%, and 75/85/95% weeks (5, 3, and 1 reps respectively) before "
        "a deload.",
    ),
    "gzclp": Term(
        "GZCLP",
        "Cody Lefever's beginner-to-intermediate linear progression program built on his GZCL "
        "method, with three tiers of lifts per session.",
        "A linear-progression program (Lefever) structuring each session as a T1 main lift, T2 "
        "secondary lift, and T3 accessory, each progressing on its own stage/rep scheme.",
    ),
    "nsuns": Term(
        "nSuns",
        "A high-volume 5/3/1 variant popularized in the lifting community, built around a heavier "
        "AMRAP top set followed by several backoff sets.",
        "A community-derived 5/3/1 variant (nSuns LP) with more total weekly sets than classic "
        "5/3/1, run off the same training-max convention.",
    ),
    "symmetry": Term(
        "symmetry",
        "How your squat/bench/deadlift compare to each other, against the ratios most balanced "
        "lifters tend to land on.",
        "A comparison of each competition lift's ratio to your deadlift (and to your total) "
        "against sex-specific expected ratios drawn from population data, flagging which lift is "
        "over- or under-represented.",
    ),
    "session_load": Term(
        "session load",
        "One workout's total training stress: however hard it felt, times how long it took.",
        "session-RPE x session duration in minutes (Foster et al., 2001) - a simple, validated "
        "proxy for a single session's training load.",
    ),
    "monotony": Term(
        "monotony",
        "How same-y your training stress was across the week - hammering the same load every day "
        "scores high, mixing hard and easy days scores low.",
        "Mean daily training load divided by its standard deviation across the week; a higher "
        "number means less day-to-day variation in load.",
    ),
    "strain": Term(
        "strain",
        "Weekly training load scaled up by monotony - a rough flag for weeks that combine a lot "
        "of work with very little variation.",
        "Weekly load x monotony (Foster et al., 2001); a descriptive training-diary number, not a "
        "validated injury-risk score.",
    ),
}


def glossary_entry(term: str) -> Term | None:
    """Look up a glossary entry by key, or by its display name (case-insensitive).

    Accepts either the internal key (`"ipf_gl"`) or the display term
    (`"IPF GL"`, `"ipf gl"`, `"ipf-gl"`) so a CLI `--term` flag can be
    forgiving about exactly how someone types it.
    """
    key = term.lower().strip().replace(" ", "_").replace("-", "_").replace("/", "")
    if key in GLOSSARY:
        return GLOSSARY[key]
    for entry in GLOSSARY.values():
        normalized = entry.term.lower().replace(" ", "_").replace("-", "_").replace("/", "")
        if normalized == key:
            return entry
    return None
