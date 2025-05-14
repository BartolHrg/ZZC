def singleton(callable): return callable();

import contextlib;
@contextlib.contextmanager
def NULL_CONTEXT_MANAGER(): yield;

class ParseError(Exception): ...

