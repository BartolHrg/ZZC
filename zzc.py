import sys;
import contextlib;
from common import *;
import parser;


typs = ["-zzc", "-src", "-hdr"];
files = {};
args = iter(sys.argv[1 : ]);
for (i, typ) in enumerate(args):
	index = 2 * i + 1;
	path = next(args);
	if typ not in typs: raise ValueError(f"File type must be one of {typs} (at {index} <{typ}>)");
	files[typ] = path;
pass
if any(typ not in files.keys() for typ in typs): raise ValueError(f"Must name all of the files: {typs}");


zzc_name = files["-zzc"];
src_name = files["-src"];
hdr_name = files["-hdr"];
with \
	open(zzc_name, "r") as zzc_file, \
	open(src_name, "w") as src_file, \
	open(hdr_name, "w") as hdr_file, \
NULL_CONTEXT_MANAGER as _:
	parser.generateSrcAndHdr(zzc_file, src_file, hdr_file);
pass
