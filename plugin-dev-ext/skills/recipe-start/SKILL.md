---
name: recipe-start
description: Orchestrate the complete ticket-to-PR development lifecycle — from requirements through implementation, quality assurance, and pull request creation. The highest-level entry point covering all phases end-to-end.
disable-model-invocation: true
---

**Context**: Full ticket-to-PR lifecycle management.

## Orchestrator Definition

**Core Identity**: "I am an orchestrator." (see subagents-orchestration-guide skill)

**Execution Protocol**:
1. **Delegate all work through Agent tool** — invoke sub-agents, pass deliverable paths between them
2. **Follow phases sequentially** — each phase gate must pass before the next begins
3. **Stop at every `[Stop: ...]` marker** → Use AskUserQuestion and wait for approval

## Current Situation Assessment

Instruction Content: $ARGUMENTS

| Situation | Decision | Next Action |
|-----------|----------|-------------|
| New ticket/requirement | No existing docs or plan | Start Phase 1 |
| Design exists, no plan | Design Doc present, no tasks | Start Phase 3 |
| Plan exists, not started | Task files present, unchecked | Start Phase 4 |
| Implementation in progress | Some tasks checked | Resume Phase 4 |
| Implementation done | All tasks checked, no PR | Start Phase 5 |

## Phase 1: Context Loading

Invoke `context-scouter` to load prior session learnings before analysis.

Pass retrieved memories as context to all subsequent agents.

## Phase 2: Requirements Analysis

```
[Stop: After requirement-analyzer — confirm scale and scope before design]
```

Invoke `requirement-analyzer` with the ticket/requirements from $ARGUMENTS and context from Phase 1.

- If `affectedLayers` includes both backend and frontend → use fullstack path (see recipe-fullstack-implement)
- If scale is `large` → proceed to PRD creation
- If scale is `medium` → proceed directly to design
- If scale is `small` → proceed directly to implementation

## Phase 3: Design

```
[Stop: After design documents created — confirm design before planning]
```

Follow the same design flow as `recipe-implement` based on scale.

## Phase 4: Implementation

Enter autonomous mode only after batch approval from user.

Follow the same per-task quality cycle as `recipe-implement`:
1. task-executor → receive response
2. Check for escalation / test review needs
3. quality-fixer → approval
4. git commit

## Phase 5: Post-Implementation QA & PR

```
[Stop: Confirm PR target branch and whether browser QA should run]
```

Invoke `recipe-pr` (or directly invoke `pr-creator` + optionally `web-qa-reviewer`).

## Phase 6: Session Learning Capture

After PR is created, invoke `context-keeper` to persist any corrections, gotchas, or project facts learned during this session.

## CRITICAL Sub-agent Invocation Constraints

**MANDATORY suffix for ALL sub-agent prompts**:
```
[SYSTEM CONSTRAINT]
This agent operates within recipe-start skill scope. Use orchestrator-provided rules only.
```
