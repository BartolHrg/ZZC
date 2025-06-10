from typing import *;

def singleton[T](callable: Callable[[], T]) -> T: return callable();

import contextlib;
@contextlib.contextmanager
def NULL_CONTEXT_MANAGER(): yield;

class ParseError(Exception): ...

def whitespaceReplacement(original: str) -> str:
	return "".join(c if c.isspace() else " " for c in original);
pass

def booleansToInt(*booleans) -> int:
	r = 0;
	for b in booleans:
		r <<= 1;
		r |= bool(b);
	pass
	return r
pass

TokenOutputer = Callable[[Any], str];

class SimpleRange:
	def __init__(self, start: int, stop: int = None):
		if stop is None: (start, stop) = (0, start);
		self.start = start;
		self.stop = stop;
	pass
	def __iter__(self): return _SimpleRangeIter(self);
	def __len__(self): return self.stop - self.start;
pass
class _SimpleRangeIter:
	def __init__(self, r: SimpleRange):
		self._r = r;
		self.next_value = r.start;
	pass
	def __next__(self):
		v = self.next_value;
		if v >= self._r.stop: raise StopIteration;
		self.next_value = v + 1;
		return v;
	pass
	def __iter__(self): return self;
	def setNext(self, value: int):
		self.next_value = value;
	pass
pass
class SimpleSliceIter[T](Iterable[tuple[int, T]]):
	def __init__(self, seq: Sequence[T], start: int = None, stop: int = None):
		self.seq = seq;
		if start is None: start = 0;
		if stop is None: stop = len(seq);
		self.rit = _SimpleRangeIter(SimpleRange(start, stop));
	pass
	def __iter__(self): return self;
	def __next__(self) -> tuple[int, T]:
		i = next(self.rit);
		return (i, self.seq[i]);
	pass
	def setNext(self, index: int): return self.rit.setNext(index);
pass

