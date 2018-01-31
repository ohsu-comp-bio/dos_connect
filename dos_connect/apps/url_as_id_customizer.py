""" default client app plugins """


def user_metadata(**kwargs):
    """ noop return user metadata """
    return None


def before_store(**kwargs):
    """ noop modify data_object """
    pass


def md5sum(**kwargs):
    """ noop return md5 """
    etag = kwargs.get('etag', None)
    return etag


def id(**kwargs):
    """ use the url as the key """
    data_object = kwargs.get('data_object', None)
    return data_object.urls[0].url
