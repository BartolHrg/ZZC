from __future__ import annotations;
from typing import *;
from common import *;

import sys, os;
import json;

from config import *;

if TYPE_CHECKING:
	from semantic import SMacroToken;
pass

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
	def src         (p: FilenameParts) -> str: return p.folder + p.name +            (".c"  if p.extension == ".zc" else ".cpp");
	@staticmethod
	def hdr         (p: FilenameParts) -> str: return p.folder + p.name +            (".h"  if p.extension == ".zc" else ".hpp");
	@staticmethod
	def inc         (p: FilenameParts) -> str: return p.folder + p.name +            (".zh" if p.extension == ".zc" else ".zzh");
	@staticmethod
	def macro_temp_1(p: FilenameParts) -> str: return p.folder + p.name + ".tmp.1" + (".c"  if p.extension == ".zc" else ".cpp");
	@staticmethod
	def macro_temp_2(p: FilenameParts) -> str: return p.folder + p.name + ".tmp.2" + (".c"  if p.extension == ".zc" else ".cpp");
	@staticmethod
	def obj         (p: FilenameParts) -> str: return p.folder + p.name + p.extension + ".o";
pass


def normpath(path: str) -> str: return os.path.normpath(path).replace("\\", "/");

if len(sys.argv) == 1:
	print("Usage python zzc.py project_root/");
	sys.exit(0);
else:
	[_, root] = sys.argv;
pass
root += "/";
root = normpath(root);

configModuleInit(root);
from config import config;

class File:
	tokens: list[SMacroToken];
	abs_file: AbsFile
	def __init__(self, path: str):
		#	print(root + "/" + config.paths.zzc);
		#	print(os.path.relpath(path, root + "/" + config.paths.zzc));
		self.path = normpath(os.path.relpath(path, root + "/" + config.paths.zzc));
		
		parts = FilenameParts(self.path);
		self.src          = file_naming.src         (parts);
		self.hdr          = file_naming.hdr         (parts);
		self.inc          = file_naming.inc         (parts);
		self.macro_temp_1 = file_naming.macro_temp_1(parts);
		self.macro_temp_2 = file_naming.macro_temp_2(parts);
		self.obj          = file_naming.obj         (parts);
		#	print(path, "        ", config.paths.zzc);
		#	print(self.path, "   ", self.inc);
		#	print(self.src, "   ", self.hdr);
		#	print(self.macro_temp_1, "   ", self.macro_temp_2);
		#	print(self.obj);
		
		self.abs_file = AbsFile(self);
	pass
	
	def relativeFile(self, path: str):
		return File(os.path.dirname(self.path) + "/" + path);
	pass
	
	def __hash__(self): return hash(self.path);
	def __eq__(self, other): return type(other) is File and self.path == other.path;
pass
class AbsFile:
	_base: File;
	def __init__(self, base: File):
		self._base = base;
	pass
	path         = property(lambda self: root + "/" + config.paths.zzc + "/" + self._base.path        );
	src          = property(lambda self: root + "/" + config.paths.cpp + "/" + self._base.src         );
	hdr          = property(lambda self: root + "/" + config.paths.cpp + "/" + self._base.hdr         );
	inc          = property(lambda self: root + "/" + config.paths.zzc + "/" + self._base.inc         );
	macro_temp_1 = property(lambda self: root + "/" + config.paths.tmp + "/" + self._base.macro_temp_1);
	macro_temp_2 = property(lambda self: root + "/" + config.paths.tmp + "/" + self._base.macro_temp_2);
	obj          = property(lambda self: root + "/" + config.paths.obj + "/" + self._base.obj         );
pass




