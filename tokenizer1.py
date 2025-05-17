from common import *;
from typing import *;
from itertools import groupby;

from dataclasses import dataclass;

class TokenType1:
	ALNUM      = 1;
	WHITESPACE = 2;
	STRING     = 3;
	COMMENT    = 4;
	MACRO      = 5;
	SYMBOL     = 6;
pass
TOKEN1_NAMES = {
	TokenType1.ALNUM     : "ALNUM     ",
	TokenType1.WHITESPACE: "WHITESPACE",
	TokenType1.STRING    : "STRING    ",
	TokenType1.COMMENT   : "COMMENT   ",
	TokenType1.MACRO     : "MACRO     ",
	TokenType1.SYMBOL    : "SYMBOL    ",
};

@dataclass
class Token1:
	typ: TokenType1;
	raw: str;
	
	def __repr__(self): return f"{TOKEN1_NAMES[self.typ]}: {self.raw.replace('\n', '\\n').replace('\t', '\\t')}";
pass

def tokenize1(zzc: str) -> Iterable[Token1]:
	tokens = _tokenize1(zzc);
	#	tokens = ((k, "".join(g)) for (k, g) in groupby(tokens, key = lambda token: token.typ));
	return list(tokens);
pass
def _tokenize1(zzc: str) -> Iterable[Token1]:
	index = 0;
	while index < len(zzc):
		try:
			(token, index) = getNextToken1(zzc, index);
			if index == 0: raise ParseError("Infinite Loop");
		except:
			print(f"Error when trying to parse from {index}: <{zzc[index : index + 10]}...>");
			raise;
		else:
			yield token;
		pass
	pass
pass

def getNextToken1(zzc: str, index: int) -> tuple[Token1, int]:
	(c, d) = (zzc + " ")[index : index + 2];
	if c.isalnum() or c == "_":
		token = "";
		for i in range(index, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if not (c.isalnum() or c == "_"): break;
			token += c;
		else:
			i += 1;
		pass
		return (Token1(TokenType1.ALNUM, token), i);
	pass
	if c.isspace() or c == "\\":
		token = "";
		for i in range(index, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if not (c.isspace() or c == "\\"): break;
			token += c;
		else:
			i += 1;
		pass
		return (Token1(TokenType1.WHITESPACE, token), i);
		typ = TokenType1.WHITESPACE;
	pass
	if c == "'":
		token = "'";
		for i in range(index + 1, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if c == "'": break;
			token += c;
		else:
			raise ParseError(IndexError);
		pass
		return (Token1(TokenType1.STRING, token + "'"), i + 1);
	pass
	if c == '"':
		token = '"';
		last_was_exc = False;
		for i in range(index + 1, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if last_was_exc:
				last_was_exc = False;
				token += c;
				continue;
			pass
			if c == "\\": last_was_exc = True;
			elif c == '"': break;
			token += c;
		else:
			raise ParseError(IndexError);
		pass
		return (Token1(TokenType1.STRING, token + '"'), i + 1);
	pass
	if c == "/" and d == "*":
		token = "/*";
		for i in range(index + 2, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if c == "*" and d == "/": break;
			token += c;
		else:
			raise ParseError(IndexError);
		pass
		return (Token1(TokenType1.COMMENT, token + "*/"), i + 2);
	pass
	if c == '/' and d == "/":
		token = '//';
		last_was_exc = False;
		for i in range(index + 1, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if c == "\n" and not last_was_exc: break;
			last_was_exc = c == "\\";
			token += c;
		else:
			i += 1
		pass
		return (Token1(TokenType1.COMMENT, token), i);
	pass
	if c == '#':
		token = '#';
		last_was_exc = False;
		for i in range(index + 1, len(zzc)):
			(c, d) = (zzc + " ")[i : i + 2];
			if c == "\n" and not last_was_exc: break;
			last_was_exc = c == "\\";
			token += c;
		else:
			i += 1
		pass
		return (Token1(TokenType1.MACRO, token), i);
	pass
	return (Token1(TokenType1.SYMBOL, c), index + 1);
pass


if __name__ == "__main__":
	import sys;
	txt = sys.stdin.read();
	for token in tokenize1(txt):
		print(token);
	pass
	#	WHITESPACE \n\t\t
	#	MACRO      #include <iostream> 
	#	WHITESPACE \n\n\t\t
	#	ALNUM      struct
	#	WHITESPACE
	#	ALNUM      S
	#	WHITESPACE
	#	SYMBOL     {
	#	WHITESPACE \n\t\t\t
	#	ALNUM      int
	#	WHITESPACE
	#	ALNUM      x
	#	SYMBOL     ;
	#	WHITESPACE \n\t\t\t
	#	COMMENT    ///\tint y;\\n\t\t\tint z;
	#	WHITESPACE \n\t\t
	#	SYMBOL     }
	#	WHITESPACE \n\t\t
	#	ALNUM      __attribute__
	#	SYMBOL     (
	#	SYMBOL     (
	#	STRING     "packed"
	#	SYMBOL     )
	#	SYMBOL     )
	#	WHITESPACE \n\t\t
	#	ALNUM      struct
	#	WHITESPACE
	#	ALNUM      S
	#	WHITESPACE
	#	SYMBOL     {
	#	WHITESPACE \n\t\t\t
	#	ALNUM      int
	#	WHITESPACE
	#	ALNUM      x
	#	WHITESPACE
	#	SYMBOL     =
	#	WHITESPACE
	#	ALNUM      1
	#	SYMBOL     ;
	#	WHITESPACE  \\n\t\t
	#	SYMBOL     }
	#	WHITESPACE
	#	ALNUM      a
	#	SYMBOL     ;
	#	WHITESPACE \n\t\t
	#	MACRO      # define ABC \\n\t\tDEF
	#	WHITESPACE \n\t\t
	#	MACRO      # include <xyz>
	#	WHITESPACE \n\t\t
	#	STRING     "abc\\n\\\" def"
	#	WHITESPACE \n\t\t
	#	COMMENT    /* \n\t\t/* \n\t\t#\n\t\t"\n\t\t*/
	#	WHITESPACE \n\t
pass
