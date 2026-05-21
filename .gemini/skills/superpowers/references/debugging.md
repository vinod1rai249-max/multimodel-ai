# Systematic Debugging

## The Workflow
1. **Reproduce**: Create a reliable, minimal reproduction of the bug.
2. **Observe**: Gather data (logs, traces, state) from the reproduction.
3. **Hypothesize**: Formulate a theory about why the bug is happening.
4. **Test**: Run an experiment to confirm or refute the hypothesis.
5. **Fix**: Once the root cause is confirmed, apply the minimal fix.
6. **Verify**: Run the reproduction and all related tests.

## Key Principles
- Don't guess.
- Isolate variables.
- One change at a time.
