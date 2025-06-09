from __future__ import annotations;
from common import *;
from typing import *;

import copy;
from itertools import chain;

from tokenizer import TokenType, Token;
from macro_processor import MacroToken, MacroType, RToken, RegionInfo, region_markers;
from forward_declaration import FwdRegistry;

class SemanticType:
	OTHER     =  0;
	NAMESPACE =  1;
	STRUCT    =  2;
	ENUM      =  4;
	USING     =  5;
	TEMPLATE  =  6;
	TYPEDEF   =  7;
	FRIEND    =  8;
	VAR       =  9;
	FUN       = 10;
	MACRO     = 11;
pass
SEMANTIC_NAMES = {
	SemanticType.OTHER    : "OTHER    ",
	SemanticType.NAMESPACE: "NAMESPACE",
	SemanticType.STRUCT   : "STRUCT   ",
	SemanticType.ENUM     : "ENUM     ",
	SemanticType.USING    : "USING    ",
	SemanticType.TEMPLATE : "TEMPLATE ",
	SemanticType.TYPEDEF  : "TYPEDEF  ",
	SemanticType.FRIEND   : "FRIEND   ",
	SemanticType.VAR      : "VAR      ",
	SemanticType.FUN      : "FUN      ",
	SemanticType.MACRO    : "MACRO    ",
};

class SematicRegions:
	fwd     : str = "";
	
	src_decl: str = "";
	src_impl: str = "";
	
	hdr_decl: str = "";
	hdr_impl: str = "";
pass
sematic_region_keys = SematicRegions.__annotations__.keys();

class SemanticStack:
	struct_prefix: str = "";
	anonymous: int = 0;
	in_struct: int = 0;
	template : int = 0;
	inline   : int = 0;
	static   : int = 0;
	
	copy = copy.copy; #	if you will modify semantic_stack, make a copy and modify copy
pass
class SToken(RToken):
	fwd: FwdRegistry | None; #	if fwd is not None, insert fwd after this token
	region: SematicRegions;
	ephermal: bool;
	should_be_included_in_var: bool;
	#	semantic_stack: SemanticStack;
	#	semantic_info: SemanticInfo;
pass
class SMacroToken(SToken, MacroToken): pass;

EPHERMALS = (TokenType.MACRO, TokenType.COMMENT, TokenType.WHITESPACE);

def semanticAnalysis(tokens: list[RToken]): 
	for token in tokens:
		token: SToken;
		token.fwd = None;
		token.region = SematicRegions();
		token.ephermal = token.typ in EPHERMALS;
		token.should_be_included_in_var = False;
	pass
	tokens: list[SToken];
	semantic_stack = SemanticStack();
	fwd = FwdRegistry(0);
	token0 = SToken(TokenType.WHITESPACE, "");
	#	RToken
	token0.declared_region = RegionInfo();
	#	SToken
	token0.fwd = fwd;
	token0.region = SematicRegions();
	token0.ephermal = True;
	tokens.insert(0, token0);
	if (r := _semanticAnalysisRecursion(tokens, 1, len(tokens), semantic_stack, fwd)) != len(tokens):
		raise ParseError(r);
	pass
	
	for token in tokens:
		regions = {key: getattr(token.declared_region, key) for key in region_markers if key not in ("zzc", "ide", )};
		if any(regions.values()):
			raw = token.raw;
			reg = token.region = SematicRegions();
			for (k, v) in regions.items():
				if v: setattr(reg, k, raw);
				else: setattr(reg, k, "");
			pass
			if token.ephermal:
				token.ephermal = False;
				token.region.fwd = raw;
			pass
		pass
	pass
pass
def _semanticAnalysisRecursion(tokens: list[SToken], index: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	while index < endex:
		i = _parseNextUnit(tokens, index, endex, semantic_stack, fwd);
		fwd.cancelCandidates();
		if i == index: raise ParseError;
		index = i;
	pass
	return endex;
pass
def _parseNextUnit(tokens: list[SToken], index: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	#	first = tokens[index];
	for (i, token) in (it := SimpleSliceIter(tokens, index, endex)):
		raw = token.raw;
		if token.typ in EPHERMALS: continue;
		#	if token.raw in "={;": return _possibleVarFun(tokens, index, endex, semantic_stack);
		if raw == ";"                             : return _vars                  (tokens, index, i,        semantic_stack, fwd);
		if raw in "<([{": 
			it.setNext(_findClosing(tokens, i));
			continue;
		pass
		if token.typ != TokenType.ALNUM: continue;
		if raw == "fun"                           : return _function              (tokens, index, i, endex, semantic_stack, fwd);
		if raw == "namespace"                     : return _namespace             (tokens, index, i, endex, semantic_stack, fwd);
		if raw == "template"                      : return _template              (tokens, index, i, endex, semantic_stack, fwd);
		if raw == "friend"                        : return _friend                (tokens, index, i, endex, semantic_stack, fwd);
		#	if raw == "enum"                          : return _enum                  (tokens, index, i, endex, semantic_stack, fwd);
		#	if raw in ("struct", "class", "union", )  : return _struct                (tokens, index, i, endex, semantic_stack, fwd);
		if raw in ("using", "typedef", "concept", ): return _using_typedef_concept(tokens, index,    endex, semantic_stack, fwd);
		if semantic_stack.in_struct and raw in ("public", "private", "protected"):
			index_colon = _tokenIndex(tokens, ":", i + 1);
			colon = tokens[index_colon];
			for t in [token, colon]:
				if semantic_stack.anonymous: t.region.src_decl = t.raw;
				else                       : t.region.hdr_decl = t.raw;
			pass
			return index_colon + 1;
		pass
	pass
	return endex;
pass

def _vars(tokens: list[SToken], index: int, index_semicolon: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	semantic_stack = semantic_stack.copy();
	commas: list[int] = [index];
	static_eligible = True;
	static = False;
	inline = False;
	for (i, token) in (it := SimpleSliceIter(tokens, index, index_semicolon + 1)):
		if token.typ in EPHERMALS: continue;
		if is_notaname(token):
			it.setNext(is_notaname.skip(tokens, i));
			continue;
		pass
		if static_eligible and token.raw == "static"   : static = True;
		if static_eligible and token.raw == "inline"   : inline = True;
		if static_eligible and token.raw == "constexpr": inline = True;
		if token.raw in ",;({=": static_eligible = False;
		if token.raw in ",;": commas.append(i);
		if token.raw in "<([{": it.setNext(_findClosing(tokens, i));
	pass
	semantic_stack.static += static;
	semantic_stack.inline += inline;
	context = booleansToInt(semantic_stack.anonymous, semantic_stack.template, semantic_stack.in_struct, static, inline);
	for i in range(len(commas) - 1):
		(a, b) = commas[i : i + 2];
		_var(tokens, a, b, semantic_stack, fwd, context);
	pass
	return index_semicolon + 1;
pass
def _var(tokens: list[SToken], index: int, index_comma: int, semantic_stack: SemanticStack, fwd: FwdRegistry, context: int):
	index_name = None;
	index_struct = None;
	has_init = False;
	extern_insert = index; #	extern does not clash with struct, since, if struct has no body, it's in impl and there is no extern
	
	for (i, token) in (it := SimpleSliceIter(tokens, index, index_comma)):
		if token.raw in ("struct", "class", "union", "enum", ): 
			index_struct = i;
			it.setNext(_enum_struct_skip(tokens, i, index_comma + 1));
			index_name = None;
			continue;
		elif token.raw == "extern":
			extern_insert = None;
		elif token.typ == TokenType.MACRO and extern_insert is not None:
			token: SMacroToken;
			if token.macro_type != MacroType.DEFINE:
				extern_insert = i + 1;
			pass
		elif is_notaname(token):
			j = is_notaname.skip(tokens, i)
			if token.raw == "requires":
				extern_insert = j
			pass
			it.setNext(j);
		elif token.raw in "<[":
			i = _findClosing(tokens, i);
			it.setNext(i);
		elif token.raw == "(":
			eligible_for_name = False;
			for (j, t) in SimpleSliceIter(tokens, i + 1, index_comma):
				if t.typ == TokenType.ALNUM:
					eligible_for_name = False;
					break;
				pass
				if t.typ == TokenType.SYMBOL:
					eligible_for_name = True;
					break;
				pass
			pass
			if not eligible_for_name:
				raise ParseError; #	dissalow `Type var(args);` because it might be confused with `Type stuff (var);`
				#	e.g. how do we know what is the name here int a (*b) (is it a initialized with *b or is it b as pointer to int a)
				has_init = True;
				break;
			pass
		elif token.raw in "{=":
			has_init = True;
			break;
		elif token.typ == TokenType.ALNUM:
			index_name = i;
		pass
	pass
	
	if index_name is None:
		if index_struct is not None:
			if tokens[index_struct].raw == "enum": _enum  (tokens, index, index_struct, index_comma + 1, semantic_stack, fwd, False);
			else:                                  _struct(tokens, index, index_struct, index_comma + 1, semantic_stack, fwd, False);
		pass
		return;
	pass
	
	if extern_insert is not None:
		for (extern_insert, tt) in SimpleSliceIter(tokens, extern_insert, index_name):
			if tt.typ == TokenType.WHITESPACE: continue;
			if tt.typ == TokenType.MACRO: 
				tt: SMacroToken;
				if tt.macro_type != MacroType.DEFINE:
					continue;
				pass
			pass
			break;
		pass
	pass
	
	hole = ();
	if index_struct is not None:
		if tokens[index_struct].raw == "enum": hole = range(index_struct, _enum  (tokens, index, index_struct, index_comma + 1, semantic_stack, fwd, True));
		else:                                  hole = range(index_struct, _struct(tokens, index, index_struct, index_comma + 1, semantic_stack, fwd, True));
	pass
	
	if has_init:
		index_init = i;
	else:
		index_init = index_comma;
	pass
	
	#	b              bi     ib
	#	|              ||     ||
	#	some_stuff name = value,
	
	#	aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
	#	C++ (unlike C) requires `extern` keyword for declaration
	added_extern = " extern " if index_name is not None else "";
	
	#	set regions
	for (i, token) in chain(SimpleSliceIter(tokens, index, index_init), [(index_comma, tokens[index_comma])]):
		raw = decl = impl = token.raw;
		region = token.region;
		if token.should_be_included_in_var:
			if type(token.should_be_included_in_var) is str:
				impl = token.should_be_included_in_var;
			pass
		elif i in hole:
			continue;
		pass
		#	anonymous template in_struct static inline
		if   context == 0b00000:
			region.hdr_decl = decl;
			region.src_impl = impl;
			if extern_insert == i:
				tokens[extern_insert].region.hdr_decl = added_extern + tokens[extern_insert].region.hdr_decl;
				added_extern = "";
			pass
		elif context == 0b00001:
			region.hdr_decl = decl;
			region.hdr_impl = impl;
			if extern_insert == i:
				tokens[extern_insert].region.hdr_decl = added_extern + tokens[extern_insert].region.hdr_decl;
				added_extern = "";
			pass
		elif context == 0b00010:
			region.src_decl = raw;
		elif context == 0b00011:
			region.hdr_decl = raw;
		elif context == 0b00100:
			region.hdr_decl = raw;
		elif context == 0b00101:
			region.hdr_decl = raw;
		elif context == 0b00110:
			region.hdr_decl = decl;
			region.src_impl = impl if i != index_name else semantic_stack.struct_prefix + impl;
		elif context == 0b00111:
			region.hdr_decl = raw;
		elif context == 0b01000:
			region.hdr_decl = raw;
		elif context == 0b01001:
			region.hdr_decl = raw;
		elif context == 0b01010:
			region.hdr_decl = raw;
		elif context == 0b01011:
			region.hdr_decl = raw;
		elif context == 0b01100:
			region.hdr_decl = raw;
		elif context == 0b01101:
			region.hdr_decl = raw;
		elif context == 0b01110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.hdr_decl = raw;
		elif context == 0b01111:
			region.hdr_decl = raw;
		elif context == 0b10000:
			region.src_decl = decl;
			region.src_impl = impl;
			if extern_insert == i:
				tokens[extern_insert].region.src_decl = added_extern + tokens[extern_insert].region.src_decl;
				added_extern = "";
			pass
		elif context == 0b10001:
			region.src_decl = decl;
			region.src_impl = impl;
			if extern_insert == i:
				tokens[extern_insert].region.src_decl = added_extern + tokens[extern_insert].region.src_decl;
				added_extern = "";
			pass
		elif context == 0b10010:
			region.src_decl = raw;
		elif context == 0b10011:
			region.src_decl = raw;
		elif context == 0b10100:
			region.src_decl = raw;
		elif context == 0b10101:
			region.src_decl = raw;
		elif context == 0b10110:
			region.src_decl = decl;
			region.src_impl = impl if i != index_name else semantic_stack.struct_prefix + impl;
		elif context == 0b10111:
			region.src_decl = raw;
		elif context == 0b11000:
			region.src_decl = raw;
		elif context == 0b11001:
			region.src_decl = raw;
		elif context == 0b11010:
			region.src_decl = raw;
		elif context == 0b11011:
			region.src_decl = raw;
		elif context == 0b11100:
			region.src_decl = raw;
		elif context == 0b11101:
			region.src_decl = raw;
		elif context == 0b11110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.src_decl = raw;
		elif context == 0b11111:
			region.src_decl = raw;
		pass
	pass
	#	set regions
	for (i, token) in SimpleSliceIter(tokens, index_init, index_comma):
		raw = token.raw;
		region = token.region;
		#	anonymous template in_struct static inline
		if   context == 0b00000:
			region.src_impl = raw;
		elif context == 0b00001:
			region.hdr_impl = raw;
		elif context == 0b00010:
			region.src_decl = raw;
		elif context == 0b00011:
			region.hdr_decl = raw;
		elif context == 0b00100:
			region.hdr_decl = raw;
		elif context == 0b00101:
			region.hdr_decl = raw;
		elif context == 0b00110:
			region.src_impl = raw;
		elif context == 0b00111:
			region.hdr_decl = raw;
		elif context == 0b01000:
			region.hdr_decl = raw;
		elif context == 0b01001:
			region.hdr_decl = raw;
		elif context == 0b01010:
			region.hdr_decl = raw;
		elif context == 0b01011:
			region.hdr_decl = raw;
		elif context == 0b01100:
			region.hdr_decl = raw;
		elif context == 0b01101:
			region.hdr_decl = raw;
		elif context == 0b01110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.hdr_decl = raw;
		elif context == 0b01111:
			region.hdr_decl = raw;
		elif context == 0b10000:
			region.src_impl = raw;
		elif context == 0b10001:
			region.src_impl = raw;
		elif context == 0b10010:
			region.src_decl = raw;
		elif context == 0b10011:
			region.src_decl = raw;
		elif context == 0b10100:
			region.src_decl = raw;
		elif context == 0b10101:
			region.src_decl = raw;
		elif context == 0b10110:
			region.src_impl = raw;
		elif context == 0b10111:
			region.src_decl = raw;
		elif context == 0b11000:
			region.src_decl = raw;
		elif context == 0b11001:
			region.src_decl = raw;
		elif context == 0b11010:
			region.src_decl = raw;
		elif context == 0b11011:
			region.src_decl = raw;
		elif context == 0b11100:
			region.src_decl = raw;
		elif context == 0b11101:
			region.src_decl = raw;
		elif context == 0b11110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.src_decl = raw;
		elif context == 0b11111:
			region.src_decl = raw;
		pass
	pass
	
	if index_name is not None:
		... #	TODO for template
		#	TODO i don't think i need this todo anymore
	pass
pass

def _function(tokens: list[SToken], index: int, index_kwd: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	semantic_stack = semantic_stack.copy();
	static = False;
	inline = False;
	index_name = None;
	for (i, token) in (it := SimpleSliceIter(tokens, index, endex)):
		if   token.raw == "static"   : static = True;
		elif token.raw == "inline"   : inline = True;
		elif token.raw == "constexpr": inline = True;
		elif is_notaname(token):
			it.setNext(is_notaname.skip(tokens, i));
		elif token.raw in "<[":
			i = _findClosing(tokens, i);
			it.setNext(i);
		elif token.raw == "(":
			break;
		elif token.typ == TokenType.ALNUM:
			index_name = i;
			if token.raw == "operator": 
				i = _operatorSkip(tokens, i, endex);
				break;
			pass
		pass
	pass
	semantic_stack.static += static;
	semantic_stack.inline += inline;
	if index_name is None: raise ParseError;
	
	if tokens[i].raw != "(": raise ParseError;
	index_args = i;
	endex_args = _findClosingNormal(tokens, index_args);
	has_init = False;
	indexes_of_equal: list[int] = [];
	for (i, token) in (it := SimpleSliceIter(tokens, endex_args + 1, endex)):
		if token.raw == "{":
			has_init = True;
			index_body = i;
			endex_body = _findClosingNormal(tokens, index_body);
			break;
		pass
		if token.raw == ":": #	for constructors() : member(value) {}
			has_init = True;
			index_body = i;
			j = _tokenIndex(tokens, "{", i + 1);
			endex_body = _findClosingNormal(tokens, j);
			break;
		pass
		if token.raw == ";":
			index_body = i;
			endex_body = i;
			break;
		pass
		if token.raw == "=":
			indexes_of_equal.append(i);
			for (j, t) in SimpleSliceIter(tokens, i + 1, endex):
				if t.typ not in EPHERMALS: 
					indexes_of_equal.append(j);
					break;
				pass
			pass
		pass
	pass
	
	context = booleansToInt(semantic_stack.anonymous, semantic_stack.template, semantic_stack.in_struct, static, inline);
	#	set regions
	for (i, token) in SimpleSliceIter(tokens, index, index_body):
		if i == index_kwd: continue;
		raw = token.raw;
		region = token.region;
		#	anonymous template in_struct static inline
		if   context == 0b00000:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b00001:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.hdr_impl = raw;
		elif context == 0b00010:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b00011 :
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.hdr_impl = raw;
		elif context == 0b00100:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw if i != index_name else semantic_stack.struct_prefix + raw;
		elif context == 0b00101:
			region.hdr_decl = raw;
		elif context == 0b00110:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw if i != index_name else semantic_stack.struct_prefix + raw;
		elif context == 0b00111:
			region.hdr_decl = raw;
		elif context == 0b01000:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.hdr_impl = raw;
		elif context == 0b01001:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.hdr_impl = raw;
		elif context == 0b01010:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b01011:
			region.hdr_decl = raw;
			if i in indexes_of_equal: continue;
			region.hdr_impl = raw;
		elif context == 0b01100:
			region.hdr_decl = raw;
		elif context == 0b01101:
			region.hdr_decl = raw;
		elif context == 0b01110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.hdr_decl = raw;
		elif context == 0b01111:
			region.hdr_decl = raw;
		elif context == 0b10000:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b10001:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b10010:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b10011 :
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b10100:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw if i != index_name else semantic_stack.struct_prefix + raw;
		elif context == 0b10101:
			region.src_decl = raw;
		elif context == 0b10110:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw if i != index_name else semantic_stack.struct_prefix + raw;
		elif context == 0b10111:
			region.src_decl = raw;
		elif context == 0b11000:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b11001:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b11010:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b11011:
			region.src_decl = raw;
			if i in indexes_of_equal: continue;
			region.src_impl = raw;
		elif context == 0b11100:
			region.src_decl = raw;
		elif context == 0b11101:
			region.src_decl = raw;
		elif context == 0b11110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.src_decl = raw;
		elif context == 0b11111:
			region.src_decl = raw;
		pass
	pass
	_handleDefaultArguments(tokens, index_args, endex_args);
	if has_init:
		#	set regions
		for (i, token) in SimpleSliceIter(tokens, index_body, endex_body):
			if token.typ == TokenType.COMMENT: token.ephermal = False;
			raw = token.raw;
			region = token.region;
			#	anonymous template in_struct static inline
			if   context == 0b00000:
				region.src_impl = raw;
			elif context == 0b00001:
				region.hdr_impl = raw;
			elif context == 0b00010:
				region.src_impl = raw;
			elif context == 0b00011 :
				region.hdr_impl = raw;
			elif context == 0b00100:
				region.src_impl = raw;
			elif context == 0b00101:
				region.hdr_decl = raw;
			elif context == 0b00110:
				region.src_impl = raw;
			elif context == 0b00111:
				region.hdr_decl = raw;
			elif context == 0b01000:
				region.hdr_impl = raw;
			elif context == 0b01001:
				region.hdr_impl = raw;
			elif context == 0b01010:
				region.src_impl = raw;
			elif context == 0b01011:
				region.hdr_impl = raw;
			elif context == 0b01100:
				region.hdr_decl = raw;
			elif context == 0b01101:
				region.hdr_decl = raw;
			elif context == 0b01110:
				raise ParseError("currently, this makes us sad (mark it inline)");
				region.hdr_decl = raw;
			elif context == 0b01111:
				region.hdr_decl = raw;
			elif context == 0b10000:
				region.src_impl = raw;
			elif context == 0b10001:
				region.src_impl = raw;
			elif context == 0b10010:
				region.src_impl = raw;
			elif context == 0b10011 :
				region.src_impl = raw;
			elif context == 0b10100:
				region.src_impl = raw;
			elif context == 0b10101:
				region.src_decl = raw;
			elif context == 0b10110:
				region.src_impl = raw;
			elif context == 0b10111:
				region.src_decl = raw;
			elif context == 0b11000:
				region.src_impl = raw;
			elif context == 0b11001:
				region.src_impl = raw;
			elif context == 0b11010:
				region.src_impl = raw;
			elif context == 0b11011:
				region.src_impl = raw;
			elif context == 0b11100:
				region.src_decl = raw;
			elif context == 0b11101:
				region.src_decl = raw;
			elif context == 0b11110:
				raise ParseError("currently, this makes us sad (mark it inline)");
				region.src_decl = raw;
			elif context == 0b11111:
				region.src_decl = raw;
			pass
		pass
	pass
	#	set regions
	if True:
		token = tokens[endex_body];
		raw = token.raw;
		region = token.region;
		#	anonymous template in_struct static inline
		if   context == 0b00000:
			region.hdr_decl = ";";
			region.src_impl = raw;
		elif context == 0b00001:
			region.hdr_decl = ";";
			region.hdr_impl = raw;
		elif context == 0b00010:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b00011 :
			region.hdr_decl = ";";
			region.hdr_impl = raw;
		elif context == 0b00100:
			region.hdr_decl = ";";
			region.src_impl = raw;
		elif context == 0b00101:
			region.hdr_decl = raw;
		elif context == 0b00110:
			region.hdr_decl = ";";
			region.src_impl = raw;
		elif context == 0b00111:
			region.hdr_decl = raw;
		elif context == 0b01000:
			region.hdr_decl = ";";
			region.hdr_impl = raw;
		elif context == 0b01001:
			region.hdr_decl = ";";
			region.hdr_impl = raw;
		elif context == 0b01010:
			region.hdr_decl = ";";
			region.hdr_impl = raw;
		elif context == 0b01011:
			region.hdr_decl = ";";
			region.hdr_impl = raw;
		elif context == 0b01100:
			region.hdr_decl = raw;
		elif context == 0b01101:
			region.hdr_decl = raw;
		elif context == 0b01110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.hdr_decl = raw;
		elif context == 0b01111:
			region.hdr_decl = raw;
		elif context == 0b10000:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b10001:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b10010:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b10011 :
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b10100:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b10101:
			region.src_decl = raw;
		elif context == 0b10110:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b10111:
			region.src_decl = raw;
		elif context == 0b11000:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b11001:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b11010:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b11011:
			region.src_decl = ";";
			region.src_impl = raw;
		elif context == 0b11100:
			region.src_decl = raw;
		elif context == 0b11101:
			region.src_decl = raw;
		elif context == 0b11110:
			raise ParseError("currently, this makes us sad (mark it inline)");
			region.src_decl = raw;
		elif context == 0b11111:
			region.src_decl = raw;
		pass
	pass
	
	return endex_body + 1;
pass
def _operatorSkip(tokens: list[SToken], index_kwd: int, endex: int):
	for (i, token) in SimpleSliceIter(tokens, index_kwd + 1, endex):
		if token.typ == TokenType.SYMBOL: break;
	pass
	if tokens[i].raw == "(":
		i = _tokenIndex(tokens, ")", i) + 1;
	pass
	return _tokenIndex(tokens, "(", i);
pass

def _namespace(tokens: list[SToken], index: int, index_kwd: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	semantic_stack = semantic_stack.copy();
	index_name = None;
	for (i, token) in SimpleSliceIter(tokens, index_kwd + 1, endex):
		if token.typ == TokenType.ALNUM:
			index_name = i;
			break;
		elif token.raw == "{":
			break;
		pass
	else:
		raise ParseError;
	pass
	
	if index_name is None:
		semantic_stack.anonymous += 1;
		index_scope = i;
	else:
		index_scope = _tokenIndex(tokens, "{", index_name + 1);
	pass
	endex_scope = _findClosingNormal(tokens, index_scope);
	
	for (i, token) in chain(SimpleSliceIter(tokens, index, index_scope + 1), [(endex_scope, tokens[endex_scope])]):
		token.ephermal = True;
		token.region.src_decl = token.raw;
		token.region.src_impl = token.raw;
	pass
	
	for i in chain(range(index, index_scope + 1), [endex_scope]): fwd.addCandidate(i);
	
	if _semanticAnalysisRecursion(tokens, index_scope + 1, endex_scope, semantic_stack, fwd) != endex_scope: raise ParseError;
	
	return endex_scope + 1;
pass

def _template(tokens: list[SToken], index: int, index_kwd: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	semantic_stack = semantic_stack.copy();
	
	index_args = None;
	endex_args = None;
	for (i, token) in SimpleSliceIter(tokens, index_kwd + 1, endex):
		if token.typ in EPHERMALS: continue;
		if token.raw == "<":
			index_args = i;
			endex_args = _findClosingGenerics(tokens, index_args);
			break;
		pass
		break;
	pass
	if endex_args is not None:
		endex_internal = endex_args;
	else:
		endex_internal = index_kwd + 1;
	pass
	
	for (i, token) in SimpleSliceIter(tokens, index, endex_internal):
		fwd.addCandidate(i);
	pass
	semantic_stack.template += 1;
	endex = _parseNextUnit(tokens, endex_internal, endex, semantic_stack, fwd);
	fwd.cancelCandidates();

	#	TODO template should know what regions it's child filled
	#	we can conclude this by inspecting first token that is not ephermal and that is not "fun"
	for (i, t) in SimpleSliceIter(tokens, endex_internal, endex):
		if t.ephermal: continue;
		if t.raw == "fun": continue;
		regions_to_fill = [key for key in sematic_region_keys if getattr(t.region, key)];
		break;
	pass
	for (i, token) in SimpleSliceIter(tokens, index, endex_internal):
		for key in regions_to_fill:
			setattr(token.region, key, token.raw);
		pass
	pass
	_handleDefaultArguments(tokens, index_args, endex_args);
	
	return endex;
pass

def _using_typedef_concept(tokens: list[SToken], index: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	for (i, token) in (it := SimpleSliceIter(tokens, index, endex)):
		if token.raw == ";": break;
		if token.raw in "<([{": it.setNext(_findClosing);
		if token.raw == "fun": is_function = True;
	else:
		raise ParseError;
	pass
	endex = i + 1;
	
	for (i, token) in SimpleSliceIter(tokens, index, endex):
		if semantic_stack.anonymous: token.region.src_decl = token.raw;
		else                       : token.region.hdr_decl = token.raw;
	pass
	return endex;
pass
def _friend(tokens: list[SToken], index: int, index_kwd: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry) -> int:
	#	templates and friends are interacting strangely, so
	#	DO NOT HAVE DEFINITION INSIDE TEMPLATE STRUCT/CLASS/UNION
	semantic_stack = semantic_stack.copy();
	
	for (i, token) in SimpleSliceIter(tokens, index, index_kwd + 1):
		if semantic_stack.anonymous: token.region.src_decl = token.raw;
		else                       : token.region.hdr_decl = token.raw;
	pass
	
	semantic_stack.struct_prefix = "";
	semantic_stack.in_struct -= 1;
	return _parseNextUnit(tokens, index_kwd + 1, endex, semantic_stack, fwd);
pass

def _enum_struct_skip(tokens: list[SToken], index_kwd, endex) -> int:
	for (i, token) in (it := SimpleSliceIter(tokens, index_kwd + 1, endex)):
		if token.raw == ";": return index_kwd + 1;
		if token.raw == "{": return _findClosingNormal(tokens, i) + 1;
		if token.raw in "<([": it.setNext(_findClosing(tokens, i));
	pass
	return index_kwd + 1;
pass
def _enum(tokens: list[SToken], index: int, index_kwd: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry, has_var: bool) -> int:
	endex = _tokenIndex(tokens, "}", index_kwd + 1) + 1;
	
	index_name = None; #	good enough, we treat name same as we treat kwd anyway
	for (i, token) in (it := SimpleSliceIter(tokens, index_kwd + 1, endex)):
		if token.typ in EPHERMALS: continue;
		if is_notaname(token): it.setNext(is_notaname.skip(tokens, i));
		if token.typ == TokenType.SYMBOL: break;
		if token.typ == TokenType.ALNUM: 
			index_name = i;
			break;
		pass
	pass
	has_name = index_name is not None;
	
	if has_name:
		for (i, token) in SimpleSliceIter(tokens, index, endex):
			if semantic_stack.anonymous: token.region.src_decl = token.raw;
			else                       : token.region.hdr_decl = token.raw;
		pass
		if has_var:
			tokens[index_name].should_be_included_in_var = True;
			tokens[index_kwd ].should_be_included_in_var = True;
		pass
	elif has_var:
		for (i, token) in SimpleSliceIter(tokens, index, endex):
			token.should_be_included_in_var = True;
		pass
	else:
		for (i, token) in SimpleSliceIter(tokens, index, endex):
			if semantic_stack.anonymous: token.region.src_decl = token.raw;
			else                       : token.region.hdr_decl = token.raw;
		pass
	pass
	return endex;
pass

def _struct(tokens: list[SToken], index: int, index_kwd: int, endex: int, semantic_stack: SemanticStack, fwd: FwdRegistry, has_var: bool) -> int:
	semantic_stack = semantic_stack.copy();
	
	index_name = None;
	i = index_kwd + 1;
	for (i, token) in (it := SimpleSliceIter(tokens, index_kwd + 1, endex)):
		if is_notaname(token):
			it.setNext(is_notaname.skip(tokens, i));
			continue;
		pass
		if token.typ == TokenType.ALNUM:
			index_name = i;
			i += 1;
			break;
		pass
		if token.typ == TokenType.SYMBOL:
			break;
		pass
	pass
	
	endex_fwd = None;
	for (index_scope, token) in (it := SimpleSliceIter(tokens, i, endex)):
		if token.raw == ":":
			endex_fwd = index_scope;
			continue;
		pass
		if token.raw in "<([":
			it.setNext(_findClosing(tokens, index_scope));
			continue;
		pass
		if token.raw in ";,": 
			if has_var:
				return index;
			else:
				for (i, token) in SimpleSliceIter(tokens, index, index_scope + 1):
					if semantic_stack.anonymous: token.region.src_decl = token.raw;
					else:                        token.region.hdr_decl = token.raw;
					if index_name is not None:
						fwd.add(i);
						token.region.fwd = token.raw;
					pass
				pass
				fwd.cancelCandidates();
				return index_scope + 1;
			pass
		pass
		if token.raw == "{": break;
	else:
		raise ParseError;
	pass
	endex_scope = _findClosingNormal(tokens, index_scope);
	if endex_fwd is None: endex_fwd = index_scope;
	
	
	tokens[index_scope].fwd = my_fwd = FwdRegistry(index_scope + 1);
	
	if index_name is None:
		#	even if unnamed struct, we may want to fwd
		if _semanticAnalysisRecursion(tokens, index_scope + 1, endex_scope, semantic_stack, my_fwd) != endex_scope: raise ParseError;
		for (i, token) in SimpleSliceIter(tokens, index, endex_scope + 1):
			#	overpower whatever happened in _semanticAnalysisRecursion (except fwd)
			region = token.region;
			region.fwd      = "";
			region.hdr_decl = "";
			region.hdr_impl = "";
			region.src_decl = "";
			region.src_impl = "";
			token.should_be_included_in_var = True;
		pass
		return endex_scope + 1;
	pass
	
	name = tokens[index_name].raw;
	for (i, token) in chain(SimpleSliceIter(tokens, index, index_scope + 1), [(endex_scope, tokens[endex_scope])]):
		if semantic_stack.anonymous: token.region.src_decl = token.raw;
		else                       : token.region.hdr_decl = token.raw;
	pass
	if not has_var:
		for (i, token) in SimpleSliceIter(tokens, index_scope + 1, endex):
			if semantic_stack.anonymous: token.region.src_decl = token.raw;
			else                       : token.region.hdr_decl = token.raw;
		pass
	pass
	if index_name is not None:
		for (i, token) in SimpleSliceIter(tokens, index, endex_fwd):
			fwd.add(i);
			token.region.fwd = token.raw;
		pass
		fwd.add(endex_scope);
		tokens[endex_scope].region.fwd = ";"
	pass
	

	semantic_stack.struct_prefix += name + " :: ";
	semantic_stack.in_struct += 1;
	if _semanticAnalysisRecursion(tokens, index_scope + 1, endex_scope, semantic_stack, my_fwd) != endex_scope: raise ParseError;

	if has_var:
		tokens[endex_scope].should_be_included_in_var = " " + tokens[index_kwd].raw + " " + tokens[index_name].raw + " ";
	pass
	
	return endex_scope + 1;
pass


class is_notaname:
	def __new__(cls, token: SToken):
		#	note: special treatment of requires in _var
		return token.raw in ("__attribute__", "requires", );
	pass
	@staticmethod
	def skip(tokens: list[SToken], index: int) -> int:
		i = _tokenIndex(tokens, "(", index);
		return _findClosingNormal(tokens, i) + 1;
	pass
pass
def _handleDefaultArguments(tokens: list[SToken], index_args: int, endex_args: int):
	is_default_value = False;
	for (i, token) in (it := SimpleSliceIter(tokens, index_args + 1, endex_args)):
		j = i + 1;
		if   token.raw == "=": is_default_value = True;
		elif token.raw == ",": is_default_value = False;
		elif token.raw in "<({[": 
			j = _findClosing(tokens, i) + 1;
			it.setNext(j);
		pass
		if is_default_value:
			for (k, t) in SimpleSliceIter(tokens, i, j):
				region = t.region;
				region.fwd = "";
				if region.hdr_decl:
					region.hdr_impl = "";
					region.src_decl = "";
					region.src_impl = "";
				elif region.hdr_impl:
					region.src_decl = "";
					region.src_impl = "";
				elif region.src_decl:
					region.src_impl = "";
				pass
			pass
		pass
	pass
pass

def _tokenIndex(tokens: list[Token], raw: str, index_start = 0):
	for i in range(index_start, len(tokens)):
		if tokens[i].raw == raw: return i;
	pass
	raise IndexError;
pass
def _findClosing(tokens: list[Token], index: int) -> int:
	if tokens[index].raw == "<": return _findClosingGenerics(tokens, index);
	else:                        return _findClosingNormal  (tokens, index);
pass
def _findClosingNormal(tokens: list[Token], index: int) -> int:
	stack = 0;
	for (i, token) in SimpleSliceIter(tokens, index, len(tokens)):
		if   token.raw in ")}]": stack += 1;
		elif token.raw in "({[": stack -= 1;
		if stack == 0:
			return i;
		pass
	pass
	raise ParseError;
pass
def _findClosingGenerics(tokens: list[Token], index: int) -> int:
	stack = 0;
	for (i, token) in (it := SimpleSliceIter(tokens, index, len(tokens))):
		if   token.raw == "<": stack += 1;
		elif token.raw == ">": stack -= 1;
		elif token.raw in "({[": it.setNext(_findClosingNormal(tokens, i) + 1);
		if stack == 0:
			return i;
		pass
	pass
	raise ParseError;
pass


