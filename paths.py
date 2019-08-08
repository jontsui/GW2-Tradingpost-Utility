import os
import sys


def fullpath(subdirectory):
	'''Joins the full path of the project root directory to any subdirectories.  This will only work properly 
	if this module (paths.py) is in the project root directory'''
	
	root_dir = os.path.dirname(__file__) # Directory of paths.py
	path = os.path.normpath(os.path.join(root_dir, subdirectory))
	return path + os.path.sep

# Path of SQLite database (will probably be deprecated)
database = fullpath('database')

# Path of logs folder
logs = fullpath('logs')

# Path for root directory
root = fullpath('')

watchlists = fullpath('watchlists')

if __name__ == '__main__':
	print(__file__)
	print(logs)
	print(database)
	print(watchlists)
