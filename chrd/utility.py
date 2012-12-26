# -*- coding: utf-8 -*-
# chr's utility functions

import settings
from pysql_wrapper import pysql_wrapper

def hash_pass(username, password, salt=settings.salt_password):
	import hashlib
	# This is so they can log in as Foo, FOO or fOo.
	username = username.lower()
	return hashlib.sha256(salt + password + username + salt).hexdigest()

def sql():
	"""Reuse this every time you need to do SQL stuff.
		sql().where('id', 1).get('table')
	"""
	return pysql_wrapper(db_type='sqlite', db_path=settings.sql_path)

def revision():
	# Change after modification, etc.
	return 'r7'

class Struct:
	def __init__(self, **entries): 
		self.__dict__.update(entries)

def date_strip_day(date_):
	if not '/' in date_:
		return date_
	return date_.split('/')[1]