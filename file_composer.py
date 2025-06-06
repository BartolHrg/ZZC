from __future__ import annotations;
from common import *;
from typing import *;

from tokenizer import *;
from macro_processor import *;
from semantic import *;

KeyOfSRegion = str
def compose(tokens: list[SToken], dst: KeyOfSRegion) -> Iterable[str]:
	for token in tokens:
		if getattr(token.declared_region, dst):
			result = token.raw;
		elif token.ephermal:
			result = token.raw;
		else:
			result = getattr(token.region, dst);
		pass
		yield result;
		if token.typ != TokenType.WHITESPACE and result.isspace(): continue;
		if fwd := token.fwd:
			yield from fwd.getAll(tokens);
		pass
	pass
pass
