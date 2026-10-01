<?php
/** Plugin Name: Ephemera local Docker loopback
 * Route the PoC's own HTTP calls through the Docker service.
 * Keeps the public URL and Host header intact. Local environment only.
 */
add_action('http_api_curl', function ($handle, $args, $url) {
    if (wp_get_environment_type() !== 'local') {
        return;
    }
    $parts = wp_parse_url($url);
    if (($parts['scheme'] ?? '') === 'http'
        && ($parts['host'] ?? '') === 'localhost'
        && ($parts['port'] ?? 0) === 8087) {
        curl_setopt($handle, CURLOPT_CONNECT_TO, ['localhost:8087:wordpress:80']);
    }
}, 10, 3);
