from __future__ import annotations;
from common import *;
from typing import *;

if TYPE_CHECKING:
	from semantic import SToken, SemanticType;
pass

class FwdRegistry:
	scope_start: int;
	indexes_tokens: list[int];
	candidates: list[int];
	
	def __init__(self, scope_start: int):
		self.scope_start = scope_start;
		self.indexes_tokens = [];
		self.candidates = [];
	pass
	
	def add(self, index: int): 
		self.indexes_tokens.append(index);
		self.indexes_tokens.extend(self.candidates);
		self.cancelCandidates();
	pass
	def     addCandidate(self, index: int): self.candidates.append(index);
	def cancelCandidates(self            ): self.candidates.clear();
	
	def getAll(self, tokens: list[SToken], dst: str) -> Iterable[str]:
		if not self.indexes_tokens: return;
		a = self.scope_start;
		b = max(self.indexes_tokens);
		if a == 0:
			for (i, token) in SimpleSliceIter(tokens, a, b + 1):
				if token.ephermal: yield token.raw;
				elif i in self.indexes_tokens:
					if   dst == "hdr" and (token.region.hdr_decl or token.region.hdr_impl):
						yield token.region.fwd or whitespaceReplacement(token.raw);
					elif dst == "src" and (token.region.src_decl or token.region.src_impl):
						yield token.region.fwd or whitespaceReplacement(token.raw);
					else:
						yield whitespaceReplacement(token.raw);
					pass
				else: yield whitespaceReplacement(token.raw);
			pass
		else:
			for (i, token) in SimpleSliceIter(tokens, a, b + 1):
				if token.ephermal: yield token.raw;
				elif i in self.indexes_tokens: yield token.region.fwd or whitespaceReplacement(token.raw); #	might not even need this check, since stuff has fwd if and only if it is added to some fwd
				else: yield whitespaceReplacement(token.raw);
			pass
		pass
		yield "\n";
	pass
pass
