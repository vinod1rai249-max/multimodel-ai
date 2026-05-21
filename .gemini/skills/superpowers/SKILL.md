---
name: superpowers
description: Enhances Gemini CLI with the "Superpowers" methodology, including TDD, systematic debugging, and structured planning. Use when starting new features, debugging complex issues, or needing a structured engineering approach.
---

# Superpowers

## Overview

The Superpowers skill transforms Gemini CLI into a high-performance engineering partner by enforcing proven software development methodologies. It provides structured workflows for Test-Driven Development (TDD), brainstorming, systematic debugging, and disciplined plan execution.

## Core Capabilities

### 1. Test-Driven Development (TDD)
Enforce a strict Red-Green-Refactor cycle. Always write a failing test before implementing any feature or fix.
- **Reference**: [tdd.md](references/tdd.md)

### 2. Systematic Debugging
Move away from "guess-and-check" debugging. Use empirical observation and hypothesis testing to find the root cause.
- **Reference**: [debugging.md](references/debugging.md)

### 3. Brainstorming & Design
Before writing code, explore the problem space, identify constraints, and design robust solutions.
- **Reference**: [brainstorming.md](references/brainstorming.md)

### 4. Structured Plan Execution
Break complex tasks into manageable sub-tasks with clear validation steps for each.
- **Reference**: [plan-execution.md](references/plan-execution.md)

## Usage

Trigger these superpowers by asking for them explicitly:
- "Let's use TDD to implement X."
- "Start a brainstorming session for Y."
- "Debug Z using the systematic approach."
- "Execute the plan for A."

## Workflow Decision Tree

1. **New Feature?** -> Brainstorming -> Plan -> TDD -> Execution.
2. **Bug Fix?** -> Systematic Debugging -> TDD (Reproduction) -> Fix -> Refactor.
3. **Refactoring?** -> TDD (Verify existing behavior) -> Refactor -> Verify.
