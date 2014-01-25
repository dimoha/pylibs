# -*- coding: utf-8 -*-
import fcntl, sys
def lock(lockname):
	def decorator(view_func):
		def wrapper_lock(*args, **kwargs):
			try:
				f = open(lockname, 'w')
				fcntl.lockf(f, fcntl.LOCK_EX + fcntl.LOCK_NB)
			except IOError:
				sys.exit("Process already is running.")
			return view_func(*args, **kwargs)
		wrapper_lock.view_func = view_func.view_func if hasattr(view_func, 'view_func') else view_func
		return wrapper_lock
	return decorator
