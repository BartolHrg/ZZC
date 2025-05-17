from typing import *;
from common import *;

import re;
import uuid;

from tokenizer1 import TokenType1, Token1;
import file_names;

#	gcc -E -o output input
#	we should add 
#	#define ide(...)
#	and filter based on region markers

class PragmaRegionInfo(TypedDict):
	src: bool;
	hdr: bool;
	ide: bool;
	zzc: bool;
pass
region_markers = PragmaRegionInfo.__annotations__.keys();
class IncludeInfo:
	before_filename: str;
	filename: str;
	after_filename: str;
	is_zzc: bool;
pass
class MacroToken1(Token1):
	macro_type: Literal["region"] | Literal["endregion"] | Literal["include"] | None;
	relevant_info: PragmaRegionInfo | IncludeInfo | None;
pass


class _ShouldYield(NamedTuple):
	code   : bool;
	macro  : bool;
	include: bool;
pass
class _RegionMarkerStack:
	info: PragmaRegionInfo = PragmaRegionInfo;
	stack : list[PragmaRegionInfo];
	def __init__(self):
		self.info = PragmaRegionInfo({key: False for key in region_markers});
		self.stack = [];
	pass
	#	for push & pop, we use clever trick: treat bool as int (so, we count how many times we saw each marker)
	def push(self, info: PragmaRegionInfo):
		self.stack.append(info);
		for (key, value) in info.items(): self.info[key] += value;
	pass
	def pop(self):
		info = self.stack.pop();
		for (key, value) in info.items(): self.info[key] -= value;
		if any(value < 0 for value in self.info.values()): raise ParseError;
	pass
pass
def prepareForPreprocess(tokens: list[Token1]) -> Iterable[str]:
	for token in tokens:
		if token.typ == TokenType1.MACRO: 
			_gatherMacroInfo(token);
		pass
	pass
	region_marker_stack = _RegionMarkerStack();
	def getShouldYield() -> _ShouldYield:
		info = region_marker_stack.info;
		if info["ide"]: return _ShouldYield(False, False, False);
		if info["zzc"]: return _ShouldYield(True , True , True );
		if info["src"]: return _ShouldYield(False, False, False);
		if info["hdr"]: return _ShouldYield(False, False, False);
		return _ShouldYield(True, False, True);
	pass
	should_yield = getShouldYield();
	yield "#pragma once\n";
	yield "<:::>\n";
	for (index, token) in enumerate(tokens):
		if token.typ == TokenType1.MACRO:
			token: MacroToken1;
			if token.macro_type == "include":
				if region_marker_stack.info["ide"]:
					yield whitespaceReplacement(token.raw);
					continue;
				pass
				shouldnt_yield = region_marker_stack.info["zzc"] and not region_marker_stack.info["src"] and not region_marker_stack.info["hdr"];
				if not shouldnt_yield: 
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
			elif token.macro_type == "region":
				region_marker_stack.push(token.relevant_info);
				yield f"<:::{index}>";
			elif token.macro_type == "endregion":
				region_marker_stack.pop();
				yield f"<:::{index}>";
			else:
				if region_marker_stack.info["ide"]:
					yield whitespaceReplacement(token.raw);
					continue;
				pass
				if region_marker_stack.info["zzc"]: 
					yield token.raw;
					if region_marker_stack.info["src"] or region_marker_stack.info["hdr"]: yield f"\n<:::{index}>";
				else: yield f"<:::{index}>";
			pass
		elif token.typ == TokenType1.COMMENT:
			yield f"<:::{index}>"; #	TODO do we need this?
		elif token.typ == TokenType1.WHITESPACE:
			yield token.raw;
		else:
			if region_marker_stack.info["ide"]:
				yield whitespaceReplacement(token.raw);
				continue;
			pass
			if region_marker_stack.info["src"] or region_marker_stack.info["hdr"]: yield f"<:::{index}>";
			else: yield token.raw;
		pass
	pass
	yield "\n<:::>";
pass
def _gatherMacroInfo(token: MacroToken1):
	raw = token.raw;
	token.macro_type = None;
	token.relevant_info = None;
	if False: pass;
	elif match := re.match(r"#[\s\\]*pragma[\s\\]*region[\s\\]*zzc", raw):
		token.macro_type = "region";
		words = re.split(r"\b", raw[match.end() : ]);
		token.relevant_info = info = PragmaRegionInfo({key: key in words for key in region_markers});
	elif re.match(r"#[\s\\]*pragma[\s\\]*endregion[\s\\]*zzc", raw):
		token.macro_type = "endregion";
	elif match := re.match(r"#[\s\\]*include[\s\\]*", raw):
		token.macro_type = "include";
		c = raw[match.end()];
		start_index = match.end() + 1;
		if c == '"': end_index = raw.index('"', start_index);
		if c == '<': end_index = raw.index('>', start_index);
		token.relevant_info = info = IncludeInfo();
		info.before_filename = raw[ : start_index               ];
		info.filename        = raw[   start_index : end_index   ];
		info.after_filename  = raw[                 end_index : ];
		info.is_zzc = info.filename.endswith(".zzc") or info.filename.endswith(".zzh");
	pass
pass

def processMarkers(raw: str, original_tokens: list[Token1]) -> Iterable[str]:
	if "<:::" not in raw: return raw;
	index_start = raw.index("<:::>") + len("<:::>\n");
	endex_end = raw.rindex("<:::>") - 1;
	if endex_end < index_start: return raw;
	index = index_start;
	while (index := raw.index("<:::", index_start)) < endex_end:
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
pass
#	def processAfterPreprocess(original_tokens: list[Token1], new_tokens: list[Token1]):
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
#	def _indexOfTokenGroup(tokens: list[Token1], item: str, start = 0) -> tuple[int, int] | tuple[None, None]:
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
	from tokenizer1 import tokenize1;
	filename = sys.argv[1];
	with open(filename) as f:
		txt = f.read();
	pass
	tokens = list(tokenize1(txt));
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
