import os
import hashlib


def user_metadata(full_path):
    """ return user meta data """
    parts = full_path.split('/')
    for idx, part in enumerate(parts):
        if part == 'Patients':
            return {'patient_id': parts[idx+1]}
    return {}


def md5sum(full_path, blocksize=65536, md5filename='md5sum.txt'):
    """ lookup md5 in local file, or compute it on the fly """
    # since md5filename only found in `real` directory, use that
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
    hash = hashlib.md5()
    with open(full_path, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()
