from __future__ import annotations;
from common import *;
from typing import *;

if TYPE_CHECKING:
	from macro_processor import RToken, MacroToken;
pass


def default(token: RToken) -> str: return token.raw;

def whitespace(token: RToken) -> str: return whitespaceReplacement(token.raw);

class ClassMember(TokenOutputer):
	prefix = "";
	def addPrefix(self, namespace: str):
		self.prefix += namespace + " :: ";
	pass
	def __call__(self, token: RToken) -> str:
		return self.prefix + token.raw;
	pass
pass

def isMoreImportantOutputer(old: TokenOutputer, new: TokenOutputer) -> bool:
	return _outputerWorth(new) > _outputerWorth(old);
pass
def _outputerWorth(o: TokenOutputer):
	if o is default: return 0;
	if isinstance(o, ClassMember): return 1;
	if o is whitespace: return 3;
pass