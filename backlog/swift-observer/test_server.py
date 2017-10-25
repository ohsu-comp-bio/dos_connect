

def test_responses(client):
    """ a populated server should return evidence for this variant """
    rsp = client.get('/swift')
    assert rsp.status_code == 200

