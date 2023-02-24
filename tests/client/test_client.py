from authlib.oauth2.rfc6749 import OAuth2Token
from pytest import mark

from homeconnect_watcher.client import HomeConnectAppliance, HomeConnectClient


class TestClientToken:
    def test_save_token(self, client: HomeConnectClient):
        assert client.token_cache.is_file()

    def test_load_token(self, client: HomeConnectClient):
        token = client._load_token()
        assert isinstance(token, OAuth2Token)


class TestAuthorize:
    def test_authorization_url(self, client: HomeConnectClient):
        assert client.authorization_url.startswith("https://")


class TestAppliances:
    @mark.asyncio
    async def test_appliances(self, client: HomeConnectClient):
        appliances = await client.appliances
        assert len(appliances) > 0
        assert all(isinstance(app, HomeConnectAppliance) for app in appliances)

    @mark.asyncio
    async def test_get_appliance(self, client: HomeConnectClient):
        appliance = (await client.appliances)[0]
        assert await client.get_appliance(appliance.appliance_id) == appliance

    @mark.asyncio
    async def test_refresh_appliances(self, client: HomeConnectClient):
        client._appliances = []
        assert len(await client.appliances) == 0
        await client.refresh_appliances()
        assert len(await client.appliances) >= 0
