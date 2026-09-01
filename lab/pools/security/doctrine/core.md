# Security Doctrine

## Core Principles

### 1. Evidence First
Every finding must have a reproducible evidence path.
Claim severity without proof is noise.

### 2. Exploitability Over Theory
A finding with a demonstrated exploit path scores higher than a theoretical risk.
Practical impact > theoretical impact.

### 3. False Positive Control
Never report a finding you cannot reproduce.
Precision > recall in production. In exploration, recall > precision.

### 4. Scope Awareness
Understand the target scope before analysis.
Out-of-scope findings are wasted work.

### 5. Progressive Disclosure
Start with automated scanning, escalate to manual analysis.
Two-pass approach: quick sweep → deep dive on promising targets.

### 6. Reproducible Methodology
Every audit step must be reproducible by another worker.
If only you can reproduce it, it's not a finding — it's an opinion.
