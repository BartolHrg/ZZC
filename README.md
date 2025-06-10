# ZZC  

C/C++ precompiler to separate source and header files.  

## Usage  

Write all your code inside `.zzc` files and it will generate `.hpp` and `.cpp` files for you.  
It is similar to LZZ, but more modern and flexible.  

To use it, run `python zzc.py your/project/root`.  
For each `.zzc` file, it will generate: `.hpp`, `.cpp`, `.zzh`, `.temp.1.cpp`, `.temp.2.cpp`, and `.zzc.o` files.  
At the moment, those files are generated in the same place as the `.zzc` file, but I plan to add separation in future.  

Compiling is (currently) hardcoded in `zzc.py` using `g++` and some compiler flags.  
You may want to edit that if you want different compiler options.  

### Important notes

* You must use `fun` to denote functions (including main function)  
```c++
fun void f() {}
```
* Functions bodies are not parsed. They go as-is in appropriate place.  
* There are 4 _sections_ generated:  
  * in `.hpp` file  
    1. `hdr_decl` public declarations  
    2. `hdr_impl` inline implementations  
  * in `.cpp` file  
    3. `src_decl` private declarations  
    4. `src_impl` implementations  
* Global `static`, and anonymous namespace `namespace {...}` stuff is private (it goes in src only).  
* You can use `#pragma region zzc tag1 tag2 ...`.  
  Allowed tags are:  
  * `ide`: should be only visible to text editor, but will not be in generated files.  
  * `cpp`: should not be preprocessed by ZZC.  
  * `zzc`: should be preprocessed by ZZC. (default)  
  * `hdr`, `src`: synonyms for `hdr_impl`, `src_impl`.  
  * `hdr_decl`, `hdr_impl`, `src_decl`, `src_impl`: put region in corresponding _section_.  
  
  Tags can be combined (e.g. `#pragma region zzc src_decl src_impl`) and nested `#pragma region zzc src_decl \n #pragma region zzc src_impl`.  
  Both of these mean region will go into both _sections_.  
```c++
#pragma region zzc src_decl
    #include <header_for_src_only>
#pragma endregion zzc // zzc here is important
#pragma region zzc hdr
    //  I know what, putting static inline variable in header file, means
    //  And I will use it responsibly
    static inline int x = 0; 
#pragma endregion zzc
```
`#pragma region zzc` is stronger than `#if`.  
```c++
#pragma region zzc ide //	#if is ignored
#if 0
#pragma endregion zzc
printf("This will be printed");
#pragma region zzc ide
#endif
#pragma endregion zzc
```
The tag `zzc` is useful in cases where you use other tags, but still want ZZC to preprocess.  
```c++
//	a.zzc
#define record struct
...

//	b.zzc
#pragma region zzc src zzc
	//	this include will go to src file
	//	but defines from it will still be visible to ZZC
	#include "a.zzh"
#pragma endregion zzc

//	if zzc didn't see a.zzc, this would most likely be error, 
//	since ZZC desn't know how to parse `record`
record R {
	...
};
```
* To include other `.zzc` files, you can either include `.zzc` or `.zzh` file.  
  Only difference is that `.zzc` file will (wrongly) expose private stuff to IDE (and using them will cause error during compilation)  

## Features  
* Generate declaration and implementation for global variables, functions, class member functions, class static members.  
* Generate forward declaration for struct/class/union.  
* It supports all (many) C++ keywords and quirks (static, inline, template, concept, requires, noexcept, pure virtual, constexpr, default arguments, ...).  
* Nested classes.  
* You can have pure virtual method with definition (not in template):  
```c++
struct S {
	fun virtual void f() = 0 {
		//  code
	}
}
```

## Planned features  

* Separation of generated files (currently, all generated files are in the same folder as the `.zzc` file)  
* Generate only if needed (currently, all files are recompiled every time, even if nothing has changed)  
* Control using `.zzc.config.json`  
* Similar to `#pragma region zzc` tags, macros for the same purpose:  
```c++
fun void f() hdr_impl({ 
    printf("This body would go to header file");
});
```
* Better CLI, including command for cleaning.  

## Limitations  
Currently, the project is still young, and there may be many bugs.  
There are also some edge cases which are allowed in normal C/C++, but are not here.  

* You must use `fun` to write functions.  
* If you use static members of a template, they either must be inline, or you separate declaration and implementation yourself.  
* You can't write in-class definition of a pure virtual method (`struct S { fun virtual void f() = 0 `~~`{/*not allowed*/}`~~`};`).  
* Default arguments of a class template are not included in forward declaration of a class, so they can be only used after definition.  
  (Or you can forward declare yourself with default arguments, and not put them in definition).  
* Generated files are in the same folder as the `.zzc` file, thus cluttering the folder (I plan to change that).  

## PS  

Reason why static and pure virtual with definition are not allowed in templates is simple:  
It would be too hard to generate it (and C++ doesn't allow in-class definition of these).  

This would need to be done
```c++
//	zzc
template <typename T>
struct S {
	static int a = 5;
	fun static void b() {}
	fun virtual void v() = 0 {}
};
```
```c++
//	hdr
template <typename T>
struct S {
	static int a;
	fun static void f();
	fun virtual void v() = 0;
};
template <typename T>
int S<T> :: a = 0; // Notice S<T>
template <typename T>
void S<T> :: f() {}
template <typename T>
void s<T> :: v() {}
```
