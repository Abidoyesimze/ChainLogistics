package io.chainlogistics.sdk;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ChainLogisticsClientTest {
    @Test
    void trimsTrailingSlashFromBaseUrl() {
        ChainLogisticsClient client = new ChainLogisticsClient("test-key", "https://example.com/");

        assertEquals("https://example.com", client.getBaseUrl());
    }
}
