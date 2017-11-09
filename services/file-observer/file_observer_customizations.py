from kafka import KafkaProducer
import os
import hashlib
import re
import logging
from customizations import store, custom_args

""" """
all_checksums = {}
try:
    all_checksums = open('SMMARTData/all_checksums.tsv').read().split()
    all_checksums = dict(zip(all_checksums[0::2], all_checksums[1::2]))
except Exception as e:
    print("WARN could not open 'SMMARTData/all_checksums.tsv'")


def user_metadata(full_path):
    """ return user meta data """
    parts = full_path.split('/')
    meta = {}
    for idx, part in enumerate(parts):
        if part == 'Patients':
            meta['patient_id'] = parts[idx+1]
    if re.compile(".*_S[0-9]_.*").match(part):
        library_id = re.split('_S[0-9]_', part)[0]
        meta['library_id'] = library_id
    return meta


def md5sum(full_path, url, blocksize=65536, md5filename='md5sum.txt'):
    """ lookup md5 in local file, or compute it on the fly
        url is provided to lookup from cache
    """
    logger = logging.getLogger(__name__)
    # since md5filename only found in `real` directory, use that
    orig_path = full_path
    full_path = os.path.realpath(full_path)
    md5filename = os.path.join(os.path.dirname(full_path), md5filename)
    if os.path.isfile(md5filename):
        # hash,file_name, ...
        hashes = open(md5filename).read().split()
        # {file_name:hash, ....}
        hashes = dict(zip(hashes[1::2], hashes[0::2]))
        # get file
        basename = os.path.basename(full_path)
        if basename in hashes:
            return hashes[basename]
    if url in all_checksums:
        return all_checksums[url]
    hash = hashlib.md5()
    try:
        with open(full_path, "rb") as f:
            logger.info("*** calculating hash for {} {}".format(full_path,
                                                          orig_path))
            for block in iter(lambda: f.read(blocksize), b""):
                hash.update(block)
        return hash.hexdigest()
    except Exception as e:
        logger.warn("**** could not open {}".format(full_path))
        logger.exception(e)
        return None
