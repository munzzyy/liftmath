// Language-neutral glossary term list.
//
// Mirrors src/liftmath/glossary.py's GLOSSARY key order by hand (same
// discipline the math modules already use to stay pinned to the Python
// reference - see e.g. one-rep-max.js's header comment - applied to prose
// instead of formulas: there's no build step to enforce this automatically,
// so a change to one side should be copied into the other by hand in the
// same commit). The actual English (and, eventually, translated) text lives
// in js/i18n/en.js under the `glossary.terms.<key>.*` keys, keyed off this
// same list - this module only owns WHICH terms exist and in what order,
// the same role math/volume-landmarks.js's MUSCLES plays for muscle names.

export const GLOSSARY_TERMS = [
  "1rm",
  "e1rm",
  "consensus",
  "rir",
  "rpe",
  "amrap",
  "trainingMax",
  "hardSet",
  "mv",
  "mev",
  "mav",
  "mrv",
  "deload",
  "mesocycle",
  "recomp",
  "partition",
  "t1t2t3",
  "tdee",
  "bmr",
  "ffmi",
  "navyBf",
  "cunningham",
  "mifflin",
  "wilks",
  "dots",
  "ipfGl",
  "mcculloch",
  "strengthTier",
  "531",
  "gzclp",
  "nsuns",
  "symmetry",
  "sessionLoad",
  "monotony",
  "strain",
];
