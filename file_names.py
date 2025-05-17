from typing import *;
from common import *;

import os;

class FilenameParts:
	path: str;
	folder: str;
	name: str;
	extension: str;
	
	def __init__(self, path: str):
		self.path = path;
		basename = os.path.basename(path);
		self.folder = path[ : -len(basename)];
		if "." in basename[1:]: index = basename.rindex(".");
		else: index = len(basename);
		self.name = basename[ : index];
		self.extension = basename[index : ];
	pass
pass


class file_naming: 
	@staticmethod
	def src         (p: FilenameParts) -> str: return p.folder + p.name +             (".c"  if p.extension == ".zc" else ".cpp");
	@staticmethod
	def hdr         (p: FilenameParts) -> str: return p.folder + p.name +             (".h"  if p.extension == ".zc" else ".hpp");
	@staticmethod
	def inc         (p: FilenameParts) -> str: return p.folder + p.name +             (".zh" if p.extension == ".zc" else ".zzh");
	@staticmethod
	def macro_temp_1(p: FilenameParts) -> str: return p.folder + p.name + ".temp.1" + (".c"  if p.extension == ".zc" else ".cpp");
	@staticmethod
	def macro_temp_2(p: FilenameParts) -> str: return p.folder + p.name + ".temp.2" + (".c"  if p.extension == ".zc" else ".cpp");
pass
