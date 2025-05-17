def singleton(callable): return callable();

import contextlib;
@contextlib.contextmanager
def NULL_CONTEXT_MANAGER(): yield;

class ParseError(Exception): ...

def whitespaceReplacement(original: str) -> str:
	return "".join(c if c.isspace() else " " for c in original);
pass
