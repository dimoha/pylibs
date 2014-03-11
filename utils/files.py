# -*- coding: utf-8 -*-
import hashlib, gzip, os

def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "r+b") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            hash.update(block)
    return hash.hexdigest()

def funzip(from_file, to_file = None, need_remove = True):
    if to_file is None:
        if from_file.endswith('.gz'):
            to_file = from_file[:-3]
        
    with open(to_file, "w") as destination_file:
        with gzip.GzipFile(from_file) as f:
            while True:
                content = f.read(8096)
                if content == '':
                    break
                destination_file.write(content)
    if need_remove:
        os.remove(from_file)
        

def to_gzip(from_file, to_file = None, need_remove = True):
    if to_file is None:
        to_file = '%s.gz' % from_file 
        
    f_in = open(from_file, 'rb')
    f_out = gzip.open(to_file, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    
    if need_remove:
        os.remove(from_file)
    return to_file
        
   