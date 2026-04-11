# Modules

## Boundary Summary

| Module | Owns | Does Not Own |
|---|---|---|
| Conversations | request state, session state, summaries | retrieval logic, business side effects |
| Orchestration | workflow choice, step budgets, branching | source-of-truth domain data |
| Agents | agent registry, prompts, role contracts | direct side effects |
| Retrieval | hybrid search, filter extraction, reranking | customer/order mutation |
| Catalog | product views, attribute facts, enrichment outputs | order lifecycle |
| Customer Support | support intent semantics, escalation packaging | final order mutations |
| Orders | order adapters, action commands, approval-aware handlers | general prompt logic |
| Merchandising | internal copilot workflows, catalog suggestions | direct storefront publishing |
| Evaluations | eval sets, online signals, regressions | request serving |
| Notifications | async alerts, human handoff delivery | orchestration decisions |

## Key Rules

1. **All side effects go through typed handlers** inside `orders` or other dedicated adapter modules.
2. **Retrieval remains separate** from orchestration so it can evolve independently.
3. **Prompts belong to agent contracts**, not scattered across business modules.
4. **Existing e-commerce services stay source-of-truth systems**.
5. **Evaluations observe every workflow**, but do not participate in core request decisions.
