from common import *;
from typing import *;
from itertools import groupby;

import copy;
from dataclasses import dataclass;

class TokenType:
	ALNUM      = 1;
	WHITESPACE = 2;
	STRING     = 3;
	COMMENT    = 4;
	MACRO      = 5;
	SYMBOL     = 6;
pass
Token_NAMES = {
	TokenType.ALNUM     : "ALNUM     ",
	TokenType.WHITESPACE: "WHITESPACE",
	TokenType.STRING    : "STRING    ",
	TokenType.COMMENT   : "COMMENT   ",
	TokenType.MACRO     : "MACRO     ",
	TokenType.SYMBOL    : "SYMBOL    ",
};

@dataclass
class Token:
	typ: TokenType;
	raw: str;
	
	def __repr__(self): return f"{Token_NAMES[self.typ]}: {self.raw.replace('\n', '\\n').replace('\t', '\\t')}";
pass

def tokenize(zzc: str) -> Iterable[Token]:
	tokens = _tokenize(zzc);
	#	tokens = ((k, "".join(g)) for (k, g) in groupby(tokens, key = lambda token: token.typ));
	return list(tokens);
pass
def _tokenize(zzc: str) -> Iterable[Token]:
	index = 0;
	while index < len(zzc):
		try:
			(token, index) = getNextToken(zzc, index);
			if index == 0: raise ParseError("Infinite Loop");
		except:
			print(f"Error when trying to parse from {index}: <{zzc[index : index + 10]}...>");
			raise;
		else:
			yield token;
		pass
	pass
pass

def getNextToken(zzc: str, index: int) -> tuple[Token, int]:
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
		return (Token(TokenType.ALNUM, token), i);
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
		return (Token(TokenType.WHITESPACE, token), i);
		typ = TokenType.WHITESPACE;
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
		return (Token(TokenType.STRING, token + "'"), i + 1);
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
		return (Token(TokenType.STRING, token + '"'), i + 1);
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
		return (Token(TokenType.COMMENT, token + "*/"), i + 2);
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
		return (Token(TokenType.COMMENT, token), i);
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
		return (Token(TokenType.MACRO, token), i);
	pass
	return (Token(TokenType.SYMBOL, c), index + 1);
pass


if __name__ == "__main__":
	import sys;
	txt = sys.stdin.read();
	for token in tokenize(txt):
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
