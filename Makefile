.PHONY: validate test dev package
validate:
\tpython3 tests/validate_structure.py

test:
\t./scripts/ci.sh

dev:
\t./scripts/dev.sh

package:
\t./scripts/package.sh
