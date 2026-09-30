# The Silence Test

An audit for whether your memory system's "importance / quality / salience" metrics measure **data** or **retrieval behavior**.

## Why

A behavior-contaminated metric is dangerous not because it is inaccurate, but because it can be **anti-correlated with health**: the sicker the system, the better the report. A green dashboard does not mean the car is fine — it may mean the dashboard is broken.

## Protocol (five steps, ~half a day)

1. **Snapshot.** Record the current values of every "importance / quality / salience" metric in your system, item by item.
2. **Silence.** Suspend all retrieval for *T* days — or, if you cannot pause production, **replay history offline while intercepting every write to persistent counters**.
3. **Recompute.** Recompute the same metrics over the same items.
4. **Compare.** Item by item. Every drifting item is a behavior-contaminated item. Mark its upstream write path (usually a `∂score/∂access > 0` feedback source).
5. **Publish.** Report the result, good or bad. A system that keeps ranking signals out of persistent fields should show **zero drift**.

## Honest boundary

A **zero** result isolates access-driven contamination only. It does not by itself prove the metric is independent of all behavior — contamination arriving through other update paths must be controlled separately before independence is claimed.

## Reading the result

| Observation | Interpretation |
|---|---|
| Metrics unchanged under silence | They measure stored data (good) |
| Metrics drift under silence | They measure retrieval behavior (fix the write path) |
| Zero drift **and** no write path from access into the metric | Structurally clean — this is invariant I1 |
| Zero drift but a weak residual correlation | Shared structural cause, not a write path — check the *formula*, not the correlation |

## Implementation sketch

```python
# 1) snapshot
snap = {item_id: metric(item_id) for item_id in all_items}

# 2) silence: disable the retrieval path (feature flag, or offline replay
#    with a write interceptor on persistent counters)
with silence_retrieval(days=T):
    ...

# 3) recompute
after = {item_id: metric(item_id) for item_id in all_items}

# 4) diff
drift = [i for i in all_items if abs(after[i] - snap[i]) > eps]
print(f"{len(drift)} drifting items — these are behavior-contaminated")
```

Removing the *retrieval* is not the same as removing *all* activity: derivations, lifecycle events, and data changes should continue. Silence only the access path.
