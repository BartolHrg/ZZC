import os;
import json;
from file_names import *;
from config import *;

class Cache:
	is_new: bool;
	dependancies: dict[File, list[File]];
	
	@staticmethod
	def default():
		config = Config();
		config.is_new = True;
		config.dependancies = {};
		return config;
	pass
	@staticmethod
	def fromJson(json):
		config = Config();
		config.is_new = False;
		config.dependancies = {File(k): [File(x) for x in v] for (k, v) in json["dependancies"].items()};
		return config
	pass
	def toJson(self):
		return {
			"dependancies": {k.path: [x.path for x in v] for (k, v) in self.dependancies.items()},
		};
	pass
pass
