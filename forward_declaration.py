from __future__ import annotations;
from common import *;
from typing import *;

if TYPE_CHECKING:
	from semantic import SToken, SemanticType;
pass

class FwdRegistry:
	indexes_tokens: list[int];
	candidates: list[int];
	
	def add(self, index: int): self.indexes_tokens.append(index);
	def addCandidate(self, index: int): self.candidates.append(index);
	def cancelCandidates(self): self.candidates.clear();
	
	def getAll(self, tokens: list[SToken]) -> Iterable[str]:
		a = min(self.indexes_tokens);
		b = min(self.indexes_tokens);
		for (i, token) in SimpleSliceIter(tokens, a, b + 1):
			if token.ephermal: yield token.raw;
			elif i in self.indexes_tokens: yield token.fwd; #	might not even need this check, since stuff has fwd if and only if it is added to some fwd
			else: yield whitespaceReplacement(token.raw)
		pass
	pass
pass
