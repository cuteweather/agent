# Unit Image Audit Prompt Template (for multimodal-looker)

Use one prompt per image.

## Required Inputs
- image_path: absolute path
- unit_type: primitive | scene
- family: e.g. pacman / grouped / ungrouped / partially_grouped_config1
- target_semantics: concise unit-level target from exp_design
- must_have: list of required visual facts
- must_not_have: list of forbidden visual facts
- checks: shape / count / orientation / layout / color / boundary

## Prompt Skeleton
You are auditing one unit image for paper-stimulus reproduction.

Image: `{image_path}`
Unit type: `{unit_type}`
Family: `{family}`
Target semantics: `{target_semantics}`
Must-have facts:
1. `{must_have_1}`
2. `{must_have_2}`
Must-not-have facts:
1. `{must_not_have_1}`
2. `{must_not_have_2}`
Checks to run:
1. Shape correctness
2. Object count and visibility
3. Orientation/grouping rule
4. Layout/position relation
5. Color consistency
6. Clipping/overflow/occlusion

Return JSON only:
{
  "image": "{image_path}",
  "verdict": "pass|warning|fail",
  "problem": "string or null",
  "evidence": "string",
  "suggested_fix": "string or null"
}

Verdict rules:
- pass: all must-have satisfied and no must-not-have violation.
- warning: minor non-blocking uncertainty; core semantics still satisfied.
- fail: core semantics violated OR cannot determine core semantics.
