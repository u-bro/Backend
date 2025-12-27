import types

class DummyResponse:
    def __init__(self, status_code=200, text='OK'):
        self.status_code = status_code
        self.text = text


def test_review_anomaly_calls_requests(monkeypatch):
    called = {}

    def fake_request(method, url, json=None, timeout=None):
        called['method'] = method
        called['url'] = url
        called['json'] = json
        called['timeout'] = timeout
        return DummyResponse(200)

    monkeypatch.setattr('requests.request', fake_request)

    # import here to ensure monkeypatch applies
    from admin_service.utils.api_client import api_client

    result = api_client.review_anomaly(123, 42)
    assert result is True
    assert called['method'] == 'POST'
    assert '/api/v1/anomalies/123/review' in called['url']
    assert called['json'] == {'reviewed_by': 42}
