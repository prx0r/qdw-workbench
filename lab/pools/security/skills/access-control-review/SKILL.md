# Access Control Review Skill v1

## Purpose
Systematic review of authorization and access control mechanisms.

## Methodology

### Step 1: Map All Entry Points
1. List every public/external function
2. List every receive/fallback function
3. List every event that modifies state
4. Check for proxy/upgrade patterns

### Step 2: Identify Access Controls
For each entry point, determine:
- Who can call it? (anyone, owner, specific role, specific address)
- What checks exist? (require, assert, if revert)
- Are checks before or after state changes?

### Step 3: Find Missing Controls
- Functions that modify critical state without access checks
- Functions where access check is after state change (CEI violation)
- Functions where access can be bypassed via:
  - tx.origin spoofing
  - Delegatecall injection
  - Selfdestruct force-send
  - Flash loan governance

### Step 4: Check Role Management
- Can roles be granted by non-admin?
- Can roles be revoked by non-admin?
- Is there a role admin who can grant any role?
- Are there time-locked role changes?

### Step 5: Verify Privilege Separation
- Can a low-privilege user escalate?
- Are there admin functions callable by regular users?
- Is there proper separation between upgrade and operation?

## Common Vulnerabilities
1. Missing `onlyOwner` on `transferOwnership`
2. `tx.origin` used for authorization
3. `selfdestruct` callable by anyone
4. `delegatecall` to untrusted contracts
5. Upgradeable proxy without timelock
6. Missing two-step ownership transfer
