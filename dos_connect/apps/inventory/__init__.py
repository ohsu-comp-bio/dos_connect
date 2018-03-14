"""
inventory
==========
scrape cloud side buckets
"""
import pickle


def get_offset(bucket_name):
    """ return offset dict """
    offset = None
    try:
        with open('offset.{}.pickle'.format(bucket_name)) as data_file:
            offset = pickle.load(data_file)
    except Exception as e:
        pass
    return offset


def save_offset(offset, bucket_name):
    """ save offset dict """
    with open('offset.{}.pickle'.format(bucket_name), 'w') as data_file:
        pickle.dump(offset, data_file)
