"""
inventory
==========
scrape cloud side buckets
"""
import pickle


def get_offset():
    """ return offset dict """
    offset = None
    try:
        with open('offset.pickle') as data_file:
            offset = pickle.load(data_file)
            print offset
    except Exception as e:
        pass
    return offset


def save_offset(offset):
    """ save offset dict """
    with open('offset.pickle', 'w') as data_file:
        pickle.dump(offset, data_file)
