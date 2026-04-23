---
name: recipe-pr
description: Orchestrate pull request creation after implementation is complete — pushes branch, builds PR body from design docs and commit history, creates PR via GitHub MCP or gh CLI. Run after recipe-implement or recipe-build completes successfully.
disable-model-invocation: true
---

**Context**: Post-implementation PR creation workflow.

## Orchestrator Definition

**Core Identity**: "I am an orchestrator." (see subagents-orchestration-guide skill)

**Execution Protocol**:
1. **Delegate all work through Agent tool** — invoke sub-agents, do not directly call git or GitHub tools
2. **Stop at every `[Stop: ...]` marker** → Use AskUserQuestion for confirmation and wait for approval before proceeding

## Current Situation Assessment

Instruction Content: $ARGUMENTS

Assess current state before proceeding:

| Situation | Decision Criteria | Next Action |
|-----------|------------------|-------------|
| Implementation complete | Quality-fixer approved, tasks done | Proceed to Step 1 |
| QA requested | qaFindings argument provided | Run web-qa-reviewer first |
| PR already open | git/GitHub shows open PR for this branch | Report URL, stop |
| Uncommitted changes | `git status` shows unstaged/staged changes | Stop: ask user to commit first |

## Execution Flow

### Step 1: Optional QA [Skip if no URL provided]

```
[Stop: Confirm whether browser QA should run before creating the PR]
```

If user confirms QA:
- Invoke `web-qa-reviewer` with the app URL
- Include `qaFindings` in PR body

### Step 2: PR Creation

Invoke `pr-creator` with:
- `designDoc`: path to the Design Doc (if one exists in `docs/`)
- `baseBranch`: target branch (default `main`)
- `qaFindings`: web-qa-reviewer output (if Step 1 ran)

Pass any title/body overrides from $ARGUMENTS.

### Step 3: Report

Report the PR URL to the user.

## CRITICAL Sub-agent Invocation Constraints

**MANDATORY suffix for ALL sub-agent prompts**:
```
[SYSTEM CONSTRAINT]
This agent operates within recipe-pr skill scope. Use orchestrator-provided rules only.
```
