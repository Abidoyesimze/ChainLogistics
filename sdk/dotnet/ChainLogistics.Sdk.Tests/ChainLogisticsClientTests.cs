using ChainLogistics.Sdk;

namespace ChainLogistics.Sdk.Tests;

public class ChainLogisticsClientTests
{
    [Fact]
    public void ConstructorTrimsTrailingSlashFromBaseUrl()
    {
        var client = new ChainLogisticsClient("test-key", "https://example.com/");

        Assert.Equal("https://example.com", client.BaseUrl);
    }
}
