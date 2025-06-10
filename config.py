import os, json;

from common import *;

def configModuleInit(_root):
	global root, CONFIG_NAME, CACHE_NAME, config;
	root = _root;
	CONFIG_NAME = root + "/.zzc.config.json";
	CACHE_NAME  = root + "/.zzc.cache.json";

	if os.path.exists(CONFIG_NAME):
		with open(CONFIG_NAME) as file:
			config = Config(json.load(file));
		pass
	else:
		config = Config({});
	pass
	mirrorFolders(config);
pass


class _ConfigPaths:
	zzc: str;
	tmp: str;
	cpp: str;
	obj: str;
	exe: str;
	
	def __init__(self, json: dict):
		self.zzc = json.get("zzc", root);
		self.cpp = json.get("cpp", self.zzc);
		self.tmp = json.get("tmp", self.cpp);
		self.obj = json.get("obj", self.tmp);
		self.exe = root + "/" + json.get("exe", "a.exe");
	pass
pass
class _ConfigVars:
	def __init__(self, vars: dict = {}):
		self._vars = vars.copy();
	pass
	def resolveVars(self, json): return self._resolveVarsRecursion(json)[0];
	def _resolveVarsRecursion(self, json):
		if type(json) is dict:
			if len(json) == 1 and "var" in json.keys():
				return (self._resolveVarsRecursion(self._vars[json["var"]])[0], True);
			else:
				return ({k: self._resolveVarsRecursion(v)[0] for (k, v) in json.items()}, False);
			pass
		pass
		if type(json) is list:
			#	flat
			result = [];
			for x in json:
				(x, was_var) = self._resolveVarsRecursion(x);
				if was_var and type(x) is list:
					result.extend(x);
				else:
					result.append(x);
				pass
			pass
			return (result, False);
		pass
		return (json, False);
	pass
pass
class ConfigCommand:
	Placeholder = tuple[str, str]
	def __init__(self, json: list[str | Placeholder], vars: _ConfigVars):
		self.vars = vars;
		self.parts = json.copy();
	pass
	def __call__(self, inputs: dict[str, str | list]) -> list[str]:
		result = self.vars.resolveVars(self.parts);
		i = 0;
		while i < len(result):
			x = result[i];
			if type(x) is dict and len(x) == 1 and "file" in x.keys():
				y = inputs[x["file"]];
				if type(y) is list: 
					result[i : i+1] = y;
					i += len(y);
					continue;
				pass
				result[i] = y;
			pass
			i += 1;
		pass
		return result;
	pass
pass
class _ConfigCompilerForLanguage:
	def __init__(self, x: dict, vars: _ConfigVars):
		self.preprocess = ConfigCommand(x["preprocess"], vars);
		self.obj        = ConfigCommand(x["obj"       ], vars);
	pass
pass
class ConfigCompiler:
	c  : _ConfigCompilerForLanguage;
	cpp: _ConfigCompilerForLanguage;
	target: ConfigCommand;
	def __init__(self, json: dict, vars: _ConfigVars):
		x = {
			"c"  : {
				"preprocess": ["gcc", "-E", "-o", {"file":"out"}, {"file":"in"}],
				"obj"       : ["gcc", "-c", "-o", {"file":"out"}, {"file":"in"}],
			},
			"c++": {
				"preprocess": ["g++", "-E", "-o", {"file":"out"}, {"file":"in"}],
				"obj"       : ["g++", "-c", "-o", {"file":"out"}, {"file":"in"}],
			},
			"target"        : ["g++",       "-o", {"file":"out"}, {"file":"in"}],
		};
		major_keys = ["c", "c++"];
		minor_keys = ["preprocess", "obj", ];
		if "target" in json.keys():
			x["target"] = json["target"];
		pass
		for (key1, y) in json.items():
			if key1 == "target": continue;
			if type(y) is dict: continue;
			assert key1 in minor_keys;
			x["c"  ][key1] = y;
			x["c++"][key1] = y;
		pass
		for (key1, y) in json.items():
			if key1 == "target": continue;
			if type(y) is not dict: continue;
			for (key2, z) in y.items():
				minor = key1 if key1 in minor_keys else key2;
				major = key1 if key1 in major_keys else key2;
				assert minor in minor_keys;
				assert major in major_keys;
				x[major][minor] = z;
			pass
		pass
		
		self.c   = _ConfigCompilerForLanguage(x["c"  ], vars);
		self.cpp = _ConfigCompilerForLanguage(x["c++"], vars);
	pass
pass
class Config:
	
	def __init__(self, json: dict):
		self.vars     = _ConfigVars    (json.get("vars"    , {}));
		self.paths    = _ConfigPaths   (json.get("paths"   , {}));
		self.compiler =  ConfigCompiler(json.get("compiler", {}), self.vars);
	pass
pass



def getFileDirs(path: str) -> list[str]:
	dir_path = os.path.dirname(path);
	if not dir_path: return [];
	normalized = os.path.normpath(dir_path);
	if normalized == '.': return [];
	return normalized.split(os.sep);
pass
def mirrorFolders(config: Config):
	zzc = root + "/" + config.paths.zzc;
	tmp = root + "/" + config.paths.tmp;
	cpp = root + "/" + config.paths.cpp;
	obj = root + "/" + config.paths.obj;
	for (base, folders, files) in os.walk(zzc):
		path = os.path.relpath(base, zzc);
		if not os.path.exists(tmp + "/" + path): os.mkdir(tmp + "/" + path);
		if not os.path.exists(cpp + "/" + path): os.mkdir(cpp + "/" + path);
		if not os.path.exists(obj + "/" + path): os.mkdir(obj + "/" + path);
	pass

	target_dirs = getFileDirs(config.paths.exe);
	target_folder = root;
	for folder in target_dirs:
		target_folder += "/" + folder;
		if not os.path.exists(target_folder): os.mkdir(target_folder);
	pass
pass

config: Config;
