package io.chainlogistics.sdk;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

public class ChainLogisticsClient {
    private final String apiKey;
    private final String baseUrl;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public ChainLogisticsClient(String apiKey) {
        this(apiKey, "https://api.chainlogistics.io");
    }

    public ChainLogisticsClient(String apiKey, String baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(30)).build();
        this.objectMapper = new ObjectMapper();
    }

    public Map<String, Object> health() throws IOException, InterruptedException {
        return get("health");
    }

    public Map<String, Object> readiness() throws IOException, InterruptedException {
        return get("health/ready");
    }

    public Map<String, Object> liveness() throws IOException, InterruptedException {
        return get("health/live");
    }

    public Map<String, Object> monitoringHealth() throws IOException, InterruptedException {
        return get("health/monitoring");
    }

    public Map<String, Object> dbHealth() throws IOException, InterruptedException {
        return get("health/db");
    }

    public List<Map<String, Object>> listProducts() throws IOException, InterruptedException {
        Map<String, Object> response = get("api/v1/products");
        return objectMapper.convertValue(response.get("products"), new TypeReference<>() {});
    }

    public Map<String, Object> get(String path) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/" + path))
            .header("Authorization", "Bearer " + apiKey)
            .header("Accept", "application/json")
            .timeout(Duration.ofSeconds(30))
            .GET()
            .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() >= 400) {
            throw new IOException("API request failed with status " + response.statusCode());
        }

        return objectMapper.readValue(response.body(), new TypeReference<>() {});
    }

    String getBaseUrl() {
        return baseUrl;
    }
}
