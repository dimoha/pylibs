# -*- coding: utf-8 -*-
import hashlib, gzip, os, time
from logging import info

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
        f = gzip.GzipFile(from_file)
        while True:
            content = f.read(8096)
            if content == '':
                break
            destination_file.write(content)
    if need_remove:
        os.remove(from_file)
        

def to_gzip(from_file, to_file = None, need_remove = True, compresslevel = 5):
    if to_file is None:
        to_file = '%s.gz' % from_file 
        
    f_in = open(from_file, 'rb')
    f_out = gzip.open(to_file, 'wb', compresslevel = compresslevel)
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    
    if need_remove:
        os.remove(from_file)
    return to_file


def clean_dir(dir_path, life_days=None, exclude_dir_names=None):

    if exclude_dir_names is None:
        exclude_dir_names = []

    if os.path.isdir(dir_path):
        files = os.listdir(dir_path)
        for f in files:
            if not f.startswith('.'):
                current_path = os.path.join(dir_path, f)
                if os.path.isfile(current_path):
                    days = (int(time.time()) - int(os.path.getmtime(current_path)))/(3600*24)
                    if days >= life_days:
                        info("Remove %s (%s days > %s days)" % (current_path, days, life_days))
                        os.remove(current_path)
                elif os.path.isdir(current_path):
                    if f not in exclude_dir_names:
                        clean_dir(current_path, life_days)
                    else:
                        info('Do not clean dir "%s" from exclude_dir_list' % f)