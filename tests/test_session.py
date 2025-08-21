import asyncio

from httpx import MockTransport, Response

from hmc_orchestrator.config import Config
from hmc_orchestrator.session import HmcSession


def test_session_relogin():
    calls = {"ms": 0}

    async def handler(request):
        if request.url.path == "/rest/api/web/Logon":
            return Response(200)
        if request.url.path == "/rest/api/uom/ManagedSystem":
            calls["ms"] += 1
            if calls["ms"] == 1:
                return Response(401)
            return Response(200, json={"Items": []})
        return Response(404)

    transport = MockTransport(handler)
    cfg = Config(host="hmc", port=12443, username="user", password="pass", verify=False)

    async def run() -> None:
        session = HmcSession(cfg, transport=transport)
        resp = await session.request("GET", "/rest/api/uom/ManagedSystem")
        assert resp.status_code == 200
        assert calls["ms"] == 2
        await session.close()

    asyncio.run(run())
