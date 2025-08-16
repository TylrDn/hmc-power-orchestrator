import httpx
import respx

from hmc_power_orchestrator.hmc_client import HMCClient


@respx.mock
def test_retries() -> None:
    route = respx.get("https://hmc/api").mock(side_effect=[httpx.Response(500), httpx.Response(200, json={"items": []})])
    client = HMCClient("https://hmc", run_id="r1")
    list(client.iter_collection("/api"))
    assert route.call_count == 2
