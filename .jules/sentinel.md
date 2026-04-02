## 2024-05-24 - SQL Injection via unvalidated **kwargs
**Vulnerability:** SQL injection risk in dynamic SQL queries using dictionary unpacking `**kwargs` (like `def contains(self, **items):`). `assert` was used to validate keys against the schema, but assertions can be optimized away. The `remove` method had no validation at all.
**Learning:** Standard Python identifier constraints do not apply to dictionary keys via `**kwargs`. A malicious caller could pass `**{"malicious_key": "val"}` to inject raw column names into string formatting for queries.
**Prevention:** Explicitly validate `**kwargs` keys against known allowed schema columns using `raise ValueError` instead of `assert` before embedding them as column names into dynamic SQL conditions.
