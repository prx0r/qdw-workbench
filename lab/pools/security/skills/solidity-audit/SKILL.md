# Solidity Audit Skill v1

## Purpose
Systematic audit of Solidity smart contracts for vulnerabilities.

## Methodology

### Phase 1: Reconnaissance
1. Read the contract README and deployment scripts
2. Identify external dependencies and imports
3. Map the inheritance hierarchy
4. List all public/external functions
5. Identify access control patterns (owner, role-based, etc.)

### Phase 2: Authorization Analysis
1. Map all state-changing functions
2. For each function, identify who can call it
3. Check for missing `onlyOwner` or role checks
4. Check for tx.origin vs msg.sender issues
5. Look for privilege escalation paths

### Phase 3: Token Flow Analysis
1. Trace token inflows and outflows
2. Check for reentrancy on external calls
3. Verify slippage protection
4. Check for flash loan attack surfaces
5. Verify oracle price manipulation resistance

### Phase 4: Edge Cases
1. Zero-value edge cases
2. Max-value overflow/underflow
3. Empty address handling
4. Timestamp dependence
5. Block hash manipulation

## Known Patterns
- Reentrancy: check all `call.value`, `transfer`, `send` patterns
- Access control: check `tx.origin`, delegatecall, selfdestruct
- Oracle manipulation: check TWAP, spot price, multi-oracle designs
- Flash loans: check price oracle dependencies within same transaction

## Output Format
For each finding:
```
Title: [descriptive title]
Severity: Critical/High/Medium/Low/Informational
Location: contract/function:line
Description: [what's wrong]
Impact: [what could happen]
Exploit Path: [how to exploit]
Recommendation: [how to fix]
```
