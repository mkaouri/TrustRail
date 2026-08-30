package trustrail.dev.ping_test

import rego.v1

test_result_is_structured_allow if {
	result := data.trustrail.dev.ping.result
	result.allow == true
	result.requires_approval == false
	result.hard_deny == false
	count(result.reasons) == 0
	result.metadata.policy == "dev-ping"
}
