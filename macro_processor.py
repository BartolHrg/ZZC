from typing import *;
from common import *;

import re;
import uuid;
import copy;
from dataclasses import dataclass;

from tokenizer import TokenType, Token;
import file_names;

#	gcc -E -o output input
#	we should add 
#	#define ide(...)
#	and filter based on region markers

class RegionInfo:
	ide     : bool = False;
	zzc     : bool = False;
	cpp     : bool = False;
	
	src_decl: bool = False;
	src_impl: bool = False;
	
	hdr_decl: bool = False;
	hdr_impl: bool = False;
	
	#	_src: bool;
	#	_hdr: bool;
	
	@property
	def src(self): return (False
		or self.src_decl
		or self.src_impl
	);
	@property
	def hdr(self): return (False
		or self.hdr_decl
		or self.hdr_impl
	);
	
	@property
	def any_dst(self): return (False
		or self.src_decl
		or self.src_impl
		or self.hdr_decl
		or self.hdr_impl
	);
	
	@classmethod
	def fromDict(cls, d):
		self = cls();
		for (k, v) in d.items(): setattr(self, k, v);
		return self;
	pass
	def copy(self): return copy.copy(self);
	def __getitem__(self, key): return getattr(self, key);
	def __setitem__(self, key, value): return setattr(self, key, value);
	def keys(self): return region_markers;
	def values(self): return [self[key] for key in region_markers];
	def items(self): return [(key, self[key]) for key in region_markers];
pass
region_markers = RegionInfo.__annotations__.keys();
class RToken(Token):
	declared_region: RegionInfo;
pass
class IncludeInfo:
	before_filename: str;
	filename: str;
	after_filename: str;
	is_zzc: bool;
pass
class MacroType:
	REGION    = 1;
	ENDREGION = 2;
	INCLUDE   = 3;
	DEFINE    = 4;
pass
@dataclass
class DefineInfo:
	name: str;
	def_undef: int;
pass
class MacroToken(RToken):
	macro_type: MacroType | None;
	relevant_info: RegionInfo | IncludeInfo | DefineInfo | None;
pass


class _RegionMarkerStack:
	_info: RegionInfo;
	stack: list[RegionInfo];
	def __init__(self):
		self._info = RegionInfo();
		self.stack = [];
	pass
	#	for push & pop, we use clever trick: treat bool as int (so, we count how many times we saw each marker)
	def push(self, info: RegionInfo):
		self.stack.append(info);
		for (key, value) in info.items(): self._info[key] += value;
	pass
	def pop(self):
		info = self.stack.pop();
		for (key, value) in info.items(): self._info[key] -= value;
		if any(value < 0 for value in self._info.values()): raise ParseError;
	pass
	@property
	def info(self): return self._info.copy();
pass

def transformIntoRTokens(tokens: list[Token]):
	for token in tokens:
		if token.typ == TokenType.MACRO: 
			gatherMacroInfo(token);
		pass
	pass
	stack = _RegionMarkerStack();
	for token in tokens:
		token: RToken;
		token.declared_region = stack.info;
		
		if token.typ == TokenType.MACRO:
			token: MacroToken;
			if   token.macro_type == MacroType.REGION   : stack.push(token.relevant_info);
			elif token.macro_type == MacroType.ENDREGION: stack.pop();
		pass
	pass
pass


def prepareForPreprocess(tokens: list[RToken]) -> Iterable[str]:
	yield "#pragma once\n";
	yield "<:::>\n";
	for (index, token) in enumerate(tokens):
		reg = token.declared_region;
		if reg.ide:
			yield whitespaceReplacement(token.raw);
		elif token.typ == TokenType.MACRO:
			token: MacroToken;
			if token.macro_type == MacroType.INCLUDE:
				if reg.ide:
					yield whitespaceReplacement(token.raw);
					continue;
				pass
				should_yield = reg.zzc or (not reg.cpp and not reg.any_dst);
				if should_yield: 
					info: IncludeInfo = token.relevant_info;
					if info.is_zzc:
						new_path = file_names.file_naming.macro_temp_1(file_names.FilenameParts(info.filename));
						new_raw = info.before_filename + new_path + info.after_filename;
						id = str(uuid.uuid4());
						yield f"<:::%{index}%{id}>\n";
						yield new_raw;
						yield f"\n<:::%%{id}>"
					else:
						id = str(uuid.uuid4());
						yield f"<:::%{index}%{id}>\n";
						yield token.raw;
						yield f"\n<:::%%{id}>"
					pass
				else: 
					yield f"<:::{index}>";
				pass
			elif token.macro_type == MacroType.REGION:
				yield f"<:::{index}>";
			elif token.macro_type == MacroType.ENDREGION:
				yield f"<:::{index}>";
			elif reg.cpp or reg.any_dst:
				yield f"<:::{index}>";
			else:
				yield token.raw;
				if reg.any_dst: yield f"\n<:::{index}>";
			pass
		elif token.typ == TokenType.COMMENT:
			yield f"<:::{index}>"; #	TODO do we need this?
		elif token.typ == TokenType.WHITESPACE:
			yield token.raw;
		else:
			if reg.zzc: yield token.raw;
			elif reg.cpp or reg.any_dst: yield f"<:::{index}>";
			else: yield token.raw;
		pass
	pass
	yield "\n<:::>";
pass
def gatherMacroInfo(token: MacroToken):
	raw = token.raw;
	token.macro_type = None;
	token.relevant_info = None;
	if match := re.match(r"#[\s\\]*pragma[\s\\]*region[\s\\]*zzc\b", raw):
		token.macro_type = MacroType.REGION;
		words = re.split(r"\b", raw[match.end() : ]);
		token.relevant_info = info = RegionInfo.fromDict({key: key in words for key in region_markers});
		if not info.src and "src" in words: info.src_impl = True;
		if not info.hdr and "hdr" in words: info.hdr_impl = True;
		if "src" in words: info._src = True; #	this was made with idea to hoist #includes into decl/fwd
		if "hdr" in words: info._hdr = True; #	but only if they were in non-specific region (src or hdr)
	elif re.match(r"#[\s\\]*pragma[\s\\]*endregion[\s\\]*zzc\b", raw):
		token.macro_type = MacroType.ENDREGION;
	elif match := re.match(r"#[\s\\]*include[\s\\]*", raw):
		token.macro_type = MacroType.INCLUDE;
		c = raw[match.end()];
		start_index = match.end() + 1;
		if c == '"': end_index = raw.index('"', start_index);
		if c == '<': end_index = raw.index('>', start_index);
		token.relevant_info = info = IncludeInfo();
		info.before_filename = raw[ : start_index               ];
		info.filename        = raw[   start_index : end_index   ];
		info.after_filename  = raw[                 end_index : ];
		info.is_zzc = info.filename.endswith(".zzc") or info.filename.endswith(".zzh");
	elif m := re.match(r"#[\s\\]*define\s+(\w+)\b", raw):
		token.macro_type = MacroType.DEFINE;
		token.relevant_info = DefineInfo(m.group(1), +1);
	elif m := re.match(r"#[\s\\]*undef\s+(\w+)\b", raw):
		token.macro_type = MacroType.DEFINE;
		token.relevant_info = DefineInfo(m.group(1), -1);
	pass
pass

def processMarkers(raw: str, original_tokens: list[Token]) -> Iterable[str]:
	if "<:::>" not in raw: return raw;
	string_indexes = list(_quickFindStrings(raw));
	index_start = raw.index("<:::>") + len("<:::>\n");
	endex_end = raw.rindex("<:::>") - 1;
	if endex_end < index_start: return raw;
	index = index_start;
	while (index := _markerIndex(raw, "<:::", index_start, string_indexes)) < endex_end:
		yield raw[index_start : index];
		if match := re.match(r"(\d+)>", raw[index + len("<:::") : index + 64]):
			i = int(match.group(1));
			yield original_tokens[i].raw;
			index_start = index + len("<:::") + match.end();
		elif match := re.match(r"%(\d+)%([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})>", raw[index + len("<:::") : index + 64]):
			i = int(match.group(1));
			yield original_tokens[i].raw;
			end_marker = f"<:::%%{match.group(2)}>";
			index_start = raw.index(end_marker) + len(end_marker);
		else:
			yield "<:::";
			index_start += len("<:::");
		pass
	pass
	yield raw[index_start : endex_end]
pass
def transformMacroTokensAfterPreprocess(tokens: list[RToken]):
	for token in tokens:
		if token.typ != TokenType.MACRO: continue;
		token: MacroToken;
		if token.macro_type == MacroType.INCLUDE:
			info: IncludeInfo = token.relevant_info;
			if not info.is_zzc: continue;
			new_path = file_names.file_naming.hdr(file_names.FilenameParts(info.filename));
			token.raw = info.before_filename + new_path + info.after_filename;
		elif token.macro_type == MacroType.REGION:
			token.raw = whitespaceReplacement(token.raw);
		elif token.macro_type == MacroType.ENDREGION:
			token.raw = whitespaceReplacement(token.raw);
		elif token.macro_type == MacroType.DEFINE:
			name      = token.relevant_info.name;
			def_undef = token.relevant_info.def_undef;
			if   def_undef == +1: token.raw = f"\n#ifndef {name}\n{token.raw}\n#endif\n"
			if   def_undef == -1: token.raw = f"\n#ifdef  {name}\n{token.raw}\n#endif\n"
		pass
		pass
	pass
pass

def _markerIndex(raw: str, sub: str, index_start: int, string_indexes: list[tuple[int, int]]) -> int:
	while True:
		index = raw.index(sub, index_start);
		if any(a < index < b for (a, b) in string_indexes):
			index_start = index + 1;
		else:
			break;
		pass
	return index;
pass
def _quickFindStrings(raw: str) -> Iterable[tuple[int, int]]:
	indexes = [index for index in _findIndexesOf(raw, '"') if _countBackslashesBefore(raw, index) % 2 == 0];
	if len(indexes) % 2 != 0: raise ParseError;
	for i in range(0, len(indexes), 2):
		yield (indexes[i], indexes[i + 1]);
	pass
pass
def _findIndexesOf[T](collection: Sequence[T], item: T) -> Iterable[int]:
	index = 0;
	while True:
		try: index = collection.index(item, index);
		except ValueError: return;
		yield index;
		index += 1;
	pass
pass
def _countBackslashesBefore(string: str, index: int) -> int:
	count = 0;
	index -= 1;
	while string[index] == "\\":
		count += 1;
		index -= 1;
	pass
	return count;
pass

#	def processAfterPreprocess(original_tokens: list[Token], new_tokens: list[Token]):
#		#	TODO make sure to tokenize only stuff after first <:::> and before last (also exclude added \n)
#		result = [];
#		endex_before = 0;
#		while True:
#			(index_special, endex_special) = _indexOfTokenGroup(tokens, "<:::", endex_before);
#			if endex_special is None: 
#				result.extend(new_tokens[endex_before : ]);
#				break;
#			pass
#			result.extend(new_tokens[endex_before : index_special]);
#			if endex_special < len(new_tokens):
#				special_typ = new_tokens[endex_special];
#				if special_typ.raw.isdigit():
#					#	<:::index>
#					if endex_special + 1 < len(new_tokens) and new_tokens[endex_special + 1].raw == ">":
#						i = int(special_typ.raw);
#						result.append(original_tokens[i]);
#						endex_before = endex_special + 2;
#						continue;
#					pass
#				elif special_typ.raw == "%":
#					#	    e  1  2 3 4 5 6 7 8 910 1 2
#					#	<:::%index%hex-hex-hex-hex-hex>
#					if (endex_special + 12 < len(new_tokens) 
#						and new_tokens[endex_special +  2].raw == "%"
#						and new_tokens[endex_special +  4].raw == "-"
#						and new_tokens[endex_special +  6].raw == "-"
#						and new_tokens[endex_special +  8].raw == "-"
#						and new_tokens[endex_special + 10].raw == "-"
#						and new_tokens[endex_special + 12].raw == ">"
#					):
#						i = int(new_tokens[endex_special + 1].raw);
#						id = "".join(token.raw for token in new_tokens[endex_special + 3 : endex_special + 12]);
#						(index_end, endex_end) = _indexOfTokenGroup(new_tokens, f"<:::%%{id}>");
#						if endex_end is not None:
#							result.append(original_tokens[i]);
#							endex_before = endex_end + 1;
#							continue;
#						pass
#					pass
#				pass
#			pass
#			result.extend(new_tokens[index_special : endex_special]);
#			endex_before = endex_special;
#		pass
#		return result;
#	pass
#	def _indexOfTokenGroup(tokens: list[Token], item: str, start = 0) -> tuple[int, int] | tuple[None, None]:
#		for index in range(start, len(tokens)):
#			peek = "";
#			for i in range(index, len(tokens)):
#				if len(peek) >= len(item): break;
#				peek += tokens[i].raw;
#			else:
#				i += 1;
#			pass
#			#	if peek.startswith(item): return index;
#			if peek == item: return (index, i);
#		pass
#		return (None, None);
#	pass


if __name__ == "__main__":
	import sys;
	import subprocess;
	from tokenizer import tokenize;
	filename = sys.argv[1];
	with open(filename) as f:
		txt = f.read();
	pass
	tokens = list(tokenize(txt));
	#	for t in tokens: print(t);
	p = file_names.FilenameParts(filename);
	t1 = file_names.file_naming.macro_temp_1(p);
	t2 = file_names.file_naming.macro_temp_2(p);
	with open(t1, "w") as file:
		for x in prepareForPreprocess(tokens):
			file.write(x);
		pass
	pass
	if subprocess.run(["gcc", "-E", "-o", t2, t1]).returncode != 0: raise ZeroDivisionError;
	with open(t2) as file:
		txt2 = file.read();
	pass
	result = processMarkers(txt2, tokens);
	with open(t2 + ".2.cpp", "w") as file:
		for x in result:
			file.write(x);
		pass
	pass
pass
