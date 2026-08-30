package trustrail.dev.ping

import rego.v1

# Trivial development policy used only to prove OPA integration.
# It returns the structured PolicyEvaluation shape (not a bare boolean).
result := {
	"allow": true,
	"requires_approval": false,
	"hard_deny": false,
	"reasons": [],
	"metadata": {"policy": "dev-ping"},
}
