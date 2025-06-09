import sys, os;
import subprocess;
import contextlib;
import json;
from collections import defaultdict;
import random;

from common import *;
from file_names import *;
#	from config import config;
import tokenizer, macro_processor, semantic, file_composer;

#	typs = ["-zzc", "-src", "-hdr"];
#	files = {};
#	args = iter(sys.argv[1 : ]);
#	for (i, typ) in enumerate(args):
#		index = 2 * i + 1;
#		path = next(args);
#		if typ not in typs: raise ValueError(f"File type must be one of {typs} (at {index} <{typ}>)");
#		files[typ] = path;
#	pass
#	if any(typ not in files.keys() for typ in typs): raise ValueError(f"Must name all of the files: {typs}");


#	zzc_name = files["-zzc"];
#	src_name = files["-src"];
#	hdr_name = files["-hdr"];
#	with \
#		open(zzc_name, "r") as zzc_file, \
#		open(src_name, "w") as src_file, \
#		open(hdr_name, "w") as hdr_file, \
#	NULL_CONTEXT_MANAGER as _:
#		parser.generateSrcAndHdr(zzc_file, src_file, hdr_file);
#	pass


#	def buildDependancies() -> tuple[dict[File, list[File]], dict[File, set[File]]]:
#		#	step 1: inflate
#		inflated = {k: v.copy() for (k, v) in config.dependancies.items()};
#		for (file, dependancy) in inflated.items():
#			i = 0;
#			while i < len(dependancy):
#				dep = dependancy[i];
#				dependancy.extend(d for d in inflated.get(dep, []) if d not in dependancy)
#				i += 1;
#			pass
#		pass
#		reversed = defaultdict(set);
#		for (file, dependancies) in config.dependancies.items():
#			for f in dependancies:
#				reversed[f].add(file);
#			pass
#		pass
#		return (inflated, reversed);
#	pass
def tokenize(file: File):
	with open(file.path) as f:
		raw = f.read();
	pass
	file.tokens = list(tokenizer.tokenize(raw));
pass


zzc_files: list[File] = [];
for (base, folders, files) in os.walk(root):
	for filename in files:
		if filename.endswith(".zzc"):
			file = File(base + "/" + filename)
			if file not in zzc_files: zzc_files.append(file);
		pass
	pass
pass

#	if config.is_new:
#		for file in zzc_files:
#			tokenize(file);
#			macro_processor.transformIntoRTokens(file.tokens);
#		pass
#		for file in zzc_files:
#			config.dependancies[file] = [file.relativeFile(token.relevant_info.filename) for token in file.tokens if token.typ == tokenizer.TokenType.MACRO and token.relevant_info.is_zzc]
#		pass
#		files_to_upadte = zzc_files;
#	else:
#		(inflated, reversed) = buildDependancies();
#		...
#		files_to_upadte = [file for file in zzc_files if]
#		#	also, do 1st tokenization and RToken transform here
#	pass

#	ok, so, plan!
#	we complete File class to have automatic paths for different file types
#	we will create dependancy table (+reverse?)
#	see which files need to be updated
#	update step 1: macro preprocess all
#	update step 2: semantic

for file in zzc_files:
	with open(root + "/" + file.path) as f: raw = f.read();
	file.tokens = list(tokenizer.tokenize(raw));
	macro_processor.transformIntoRTokens(file.tokens);
	with open(root + "/" + file.macro_temp_1, "w") as f:
		for chunk in macro_processor.prepareForPreprocess(file.tokens):
			f.write(chunk);
		pass
	pass
pass
for file in zzc_files:
	r = subprocess.run(["gcc", "-E", "-o", root + "/" + file.macro_temp_2, root + "/" + file.macro_temp_1], stderr=subprocess.PIPE, text=True);
	if r.returncode != 0: 
		sys.stderr.write(r.stderr);
		raise ParseError;
	pass
pass
for file in zzc_files:
	with open(root + "/" + file.macro_temp_2) as f: raw = f.read();
	raw = "".join(macro_processor.processMarkers(raw, file.tokens));
	file.tokens = list(tokenizer.tokenize(raw));
	macro_processor.transformIntoRTokens(file.tokens);
	macro_processor.transformMacroTokensAfterPreprocess(file.tokens);
	semantic.semanticAnalysis(file.tokens);
	
	#	file_id = random.randint(1<<32, (1<<64)-1);
	with open(root + "/" + file.hdr, "w") as f, open(root + "/" + file.inc, "w") as i:
		f.write("#pragma once\n");
		i.write("#pragma once\n");
		for chunk in file_composer.compose(file.tokens, "hdr_decl"):
			f.write(chunk);
			i.write(chunk);
		pass
		f.write("\n");
		i.write("\n");
		for chunk in file_composer.compose(file.tokens, "hdr_impl"):
			f.write(chunk);
			i.write(chunk);
		pass
	pass
	with open(root + "/" + file.src, "w") as f:
		f.write(f'#include "./{file.hdr}"\n');
		for chunk in file_composer.compose(file.tokens, "src_decl"):
			f.write(chunk);
		pass
		f.write("\n");
		for chunk in file_composer.compose(file.tokens, "src_impl"):
			f.write(chunk);
		pass
	pass
pass
for file in zzc_files:
	if subprocess.run(["g++", "-c", "-Dfun=", "-Dself=(*this)", "-o", root + "/" + file.obj, root + "/" + file.src]).returncode != 0: raise ParseError;
pass
if subprocess.run(["g++", "-o", root + "/a.exe", *(root + "/" + file.obj for file in zzc_files)]).returncode != 0: raise ParseError;

