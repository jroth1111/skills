# Test Scenarios for {{SKILL_NAME}}

## Quick Test Checklist

Before deploying, verify each scenario:

### Trigger Tests (should activate)

| # | Prompt | Expected Behavior | Pass? |
|---|--------|-------------------|-------|
| 1 | "TODO: First trigger phrase" | Skill activates, follows instructions | [ ] |
| 2 | "TODO: Second trigger phrase" | Skill activates, follows instructions | [ ] |
| 3 | "TODO: Third trigger phrase" | Skill activates, follows instructions | [ ] |
| 4 | "TODO: Fourth trigger phrase" | Skill activates, follows instructions | [ ] |
| 5 | "TODO: Fifth trigger phrase" | Skill activates, follows instructions | [ ] |

### Anti-Trigger Tests (should NOT activate)

| # | Prompt | Expected Behavior | Pass? |
|---|--------|-------------------|-------|
| 1 | "TODO: First anti-trigger" | Skill does NOT activate | [ ] |
| 2 | "TODO: Second anti-trigger" | Skill does NOT activate | [ ] |
| 3 | "TODO: Third anti-trigger" | Skill does NOT activate | [ ] |

### Acceptance Test Verification

For each acceptance test in skill.spec.json, verify:

| # | Acceptance Test | Observed Behavior | Pass? |
|---|-----------------|-------------------|-------|
| 1 | "TODO: Copy from skill.spec.json" | | [ ] |
| 2 | "TODO: Copy from skill.spec.json" | | [ ] |
| 3 | "TODO: Copy from skill.spec.json" | | [ ] |

## Detailed Test Cases

### Test Case 1: Happy Path

**Setup:**
- Input: TODO
- Context: TODO

**Steps:**
1. Provide the input to Claude
2. Verify skill activates
3. Check output matches expectations

**Expected Output:**
- Files created: workspace/TODO
- Summary includes: TODO
- No errors or warnings

**Actual Result:**
- [ ] Pass / [ ] Fail
- Notes:

### Test Case 2: Edge Case - Empty Input

**Setup:**
- Input: (empty or minimal input)

**Expected Behavior:**
- Skill should ask for required information
- Should NOT crash or produce garbage output

**Actual Result:**
- [ ] Pass / [ ] Fail
- Notes:

### Test Case 3: Edge Case - Invalid Input

**Setup:**
- Input: (malformed or invalid input)

**Expected Behavior:**
- Clear error message
- Suggests how to fix

**Actual Result:**
- [ ] Pass / [ ] Fail
- Notes:

## Automated Testing

Run trigger analysis:
```bash
python /path/to/skill-creator/scripts/analyze_triggers.py {baseDir}
```

Run effectiveness evaluation:
```bash
python /path/to/skill-creator/scripts/evaluate_skill.py {baseDir}
```

## Test Results Summary

| Category | Passed | Failed | Notes |
|----------|--------|--------|-------|
| Triggers | /5 | | |
| Anti-triggers | /3 | | |
| Acceptance | /3 | | |
| Edge cases | /2 | | |

**Overall Status:** [ ] Ready for use / [ ] Needs work

**Date Tested:** ____
**Tested By:** ____
