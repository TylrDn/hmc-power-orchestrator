from hmc_power_orchestrator.policy import Policy


def test_schema_roundtrip() -> None:
    policy = Policy(policy_version=1, targets=[])
    schema = policy.to_json_schema()
    assert 'policy_version' in schema
