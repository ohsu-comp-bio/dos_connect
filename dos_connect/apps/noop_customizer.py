""" default client app plugins """


def user_metadata(**kwargs):
    """ noop return None """
    return None


def before_store(**kwargs):
    """ noop modify data_object """
    pass


def md5sum(**kwargs):
    """ noop return data_object """
    print kwargs
    return None
