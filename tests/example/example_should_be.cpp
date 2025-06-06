#include "./example_should_be.hpp"

//	fwd
namespace {
	struct X;
}
//	src_decl
namespace {
	struct X {
		int b = 0;
	};
	int a;
}
//	src_decl_with_default
namespace {
	int a; //	optional
}
//	src_decl
namespace {
	int a = 0;
}