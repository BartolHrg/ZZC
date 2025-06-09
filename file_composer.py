from __future__ import annotations;
from common import *;
from typing import *;

from tokenizer import *;
from macro_processor import *;
from semantic import *;

KeyOfSRegion = str
def compose(tokens: list[SToken], dst: KeyOfSRegion) -> Iterable[str]:
	for token in tokens:
		result = getattr(token.region, dst);
		if not result: 
			if token.ephermal: result = token.raw;
			else: result = whitespaceReplacement(token.raw);
		pass
		yield result
		if result != token.raw: continue;
		if fwd := token.fwd:
			if token.raw == "" and not dst.endswith("_decl"): continue;
			yield from fwd.getAll(tokens, dst[ : 3]);
		pass
	pass
pass
