import requests
from . import init_logging, SERVER_URL

init_logging()


def test_metrics():
    """..........OHSU metrics.............."""
    r = requests.get(SERVER_URL + 'metrics')
    assert r.status_code == 200, '/metrics should return 200'
    assert 'text/html' in r.headers['content-type'], \
        'content-type should be text/html'
    assert 'dos_connect_data_bundles_count' in r.text, \
        'should return dos_connect_data_bundles_count'
    assert 'dos_connect_data_objects_count' in r.text, \
        'should return dos_connect_data_objects_count'
