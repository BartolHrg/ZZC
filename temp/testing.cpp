#include <iostream>

#define self (*this)


template<typename _ = void>
struct C;
template<typename _ = void>
struct A;
struct B;


template<typename _>
struct A {
	struct B {
		typename C<_> :: T y;
		//	int y;
		void f(C<_> c)
		{
	std :: cout << "Hello world " << c.x << std :: endl;
}
		;
	};
};
template<typename _>
struct C {
	using T = int;
	T x;
	void f(typename A<_> :: B b)
	{
	std :: cout << "===========================" << std :: endl;
	b.f(self);
	std :: cout << "---------------------------" << std :: endl;
}
	;
};
enum Enum2 : unsigned int; 

//	void f();
//	namespace N1 {
//		void f();
//		struct Base {
//			virtual void f() /* const */ /* = 0 */ {
//				printf("base\n");
//			}
//		};
//		struct Child : Base {
//			void f() /* const */ override;
		
//			friend inline void my_friend() {}
//			struct X {
//				friend void /* Child :: */  f();
//				private:
//				void mypriv() {}
//			};
//		};
//		void f() {
//			Child :: X x;
//			x.mypriv();
//			printf("friend\n");
//		}

//		void Child :: f() /* const */ {
//			Child :: X x;
//			x.mypriv();
//			printf("child\n");
//		}
//	}
//	void f() {
//		N1 :: Child :: X x;
//		x.mypriv();
//		printf("friend\n");
//	}

namespace N2 {
	using T = int;
	using U = int;
	class S {
		friend void f(S, T, U);
		int mypriv;
	};
	void g() {
		f(S{}, 4, 5);
	}
	void f(S s, T t, U u) {
		(void) s;
		(void) t;
		(void) u;
		//	s.mypriv;
	}
}

//	template<typename _ = int>
//	void A<_> :: B :: f(C<_> c) {
//		std :: cout << "Hello world " << c.x << std :: endl;
//	}
//	template<typename _ = int>
//	void C<_> :: f(typename A<_> :: B b) {
//		std :: cout << "===========================" << std :: endl;
//		b.f(self);
//		std :: cout << "---------------------------" << std :: endl;
//	}

template <class T> concept EqualityComparable = true;
template <class T, class S> concept Same = true;
template<class T = void>
    requires (EqualityComparable<T> || Same<T, void>)
struct equal_to;


//	#line 8840 "testing.zzc"
namespace N3 {
	void f()  
	;
	//	void a;
}
//	#line 8840 "testing.zzc"
namespace N3 {
	void f() {
		//	void a;
	}
	//	void a;
}

namespace N4 {
	template <typename T>
	struct S {
		inline static T k = 0;
	};
	//	template <typename T> T S<T> :: k = 0;
}
namespace N5 {
	template <typename T>
	extern T x;
	
	template <> double x<int>;
	
	void* p1 = &x<int>;
	
	template <typename T>
	T x = T(123);
	
	void* p2 = &x<int>;
}

namespace N6 {
	template <typename T>
	T x();
	
	template <typename T>
	T x() { return T(123); }
}

namespace N7 {
	struct S {
		void f();
	};
	//	void S :: f();
	void S :: f() {}
}

namespace N8 {
	template <typename T> struct S {};
	
	template <typename T> struct S ;
}

namespace N9 {
	extern int a;
	inline int b = a + 1;
	//	int b = 77;
}
namespace N9 {
	inline int a = 8;
}

namespace N10 {
	inline void f();
	
	inline void f() {
		printf("inline f\n");
	}
	
	static void g();
	
	static void g() {
		printf("inline g\n");
	}
}

namespace N11 {
	enum {
		A, B
	} x;
}

//	#line 200 "main.cpp"
int main() {
	C c;
	c.x = 89;
	//	typename A<> :: B b; 
	//	b.y = 93;
	//	c.f(b);
	//	Child cc;
	//	cc.f();
	N4 :: S<int> s4;
	(void) s4;
	
	auto x = N5 :: x<int>;
	(void) x;
	printf("%p\n%p\n", N5 :: p1, N5 :: p2);
	
	N8 :: S<int> s8;
	(void) s8;
	
	printf("%d\n", N9 :: b);
	
	N10 :: f();
	N10 :: g();
}