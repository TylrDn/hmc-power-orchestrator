from hmc_orchestrator.policies import ScalingPolicy, decide_vcpu, decide_memory
from hmc_orchestrator.hmc_api import LparMetrics


def sample_policy() -> ScalingPolicy:
    return ScalingPolicy(
        min_vcpu=1,
        max_vcpu=8,
        scale_up_cpu_ready_pct=20,
        scale_down_cpu_idle_pct=70,
        min_mem_mb=1024,
        max_mem_mb=8192,
        scale_up_mem_free_mb=1024,
        scale_down_mem_free_mb=4096,
        step_mem_mb=1024,
        exclude_lpars=[],
    )


def test_decide_vcpu_up():
    policy = sample_policy()
    metrics = LparMetrics(cpu_idle_pct=10, cpu_ready_pct=30, mem_free_mb=0)
    assert decide_vcpu(2, metrics, policy) == 3


def test_decide_vcpu_down():
    policy = sample_policy()
    metrics = LparMetrics(cpu_idle_pct=80, cpu_ready_pct=1, mem_free_mb=0)
    assert decide_vcpu(4, metrics, policy) == 3


def test_decide_memory_up_down_bounds():
    policy = sample_policy()
    metrics_low = LparMetrics(cpu_idle_pct=0, cpu_ready_pct=0, mem_free_mb=512)
    metrics_high = LparMetrics(cpu_idle_pct=0, cpu_ready_pct=0, mem_free_mb=8192)
    # scale up
    assert decide_memory(2048, metrics_low, policy) == 3072
    # scale down but not below min
    assert decide_memory(1024, metrics_high, policy) == 1024
