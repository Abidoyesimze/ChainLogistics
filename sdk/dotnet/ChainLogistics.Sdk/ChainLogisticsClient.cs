using System.Net.Http.Headers;
using System.Text.Json;

namespace ChainLogistics.Sdk;

public class ChainLogisticsClient
{
    private readonly HttpClient _httpClient;

    public ChainLogisticsClient(string apiKey, string baseUrl = "https://api.chainlogistics.io", HttpClient? httpClient = null)
    {
        BaseUrl = baseUrl.TrimEnd('/');
        _httpClient = httpClient ?? new HttpClient();
        _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
        _httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
    }

    public string BaseUrl { get; }

    public Task<JsonDocument> HealthAsync(CancellationToken cancellationToken = default) => GetAsync("health", cancellationToken);

    public Task<JsonDocument> ReadinessAsync(CancellationToken cancellationToken = default) => GetAsync("health/ready", cancellationToken);

    public Task<JsonDocument> LivenessAsync(CancellationToken cancellationToken = default) => GetAsync("health/live", cancellationToken);

    public Task<JsonDocument> MonitoringHealthAsync(CancellationToken cancellationToken = default) => GetAsync("health/monitoring", cancellationToken);

    public Task<JsonDocument> DbHealthAsync(CancellationToken cancellationToken = default) => GetAsync("health/db", cancellationToken);

    public Task<JsonDocument> ListProductsAsync(CancellationToken cancellationToken = default) => GetAsync("api/v1/products", cancellationToken);

    public async Task<JsonDocument> GetAsync(string path, CancellationToken cancellationToken = default)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, $"{BaseUrl}/{path}");
        using var response = await _httpClient.SendAsync(request, cancellationToken);
        response.EnsureSuccessStatusCode();

        var body = await response.Content.ReadAsStringAsync(cancellationToken);
        return JsonDocument.Parse(body);
    }
}
