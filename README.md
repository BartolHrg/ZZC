# ZZC  

C/C++ precompiler to separate source and header files.  

## Usage  

Write all your code inside `.zzc` files and it will generate `.hpp` and `.cpp` files for you.  
It is similar to LZZ, but more modern and flexible.  

C++ files should end with `.zzc` and C files with `.zc` (Although, for now, C is probably supported).  

To use it, run `python zzc.py your/project/root`.  
For each `.zzc` file, it will generate: `.hpp`, `.cpp`, `.zzh`, `.tmp.1.cpp`, `.tmp.2.cpp`, and `.zzc.o` files.  
At the moment, those files are generated in the same place as the `.zzc` file, but I plan to add separation in the future.  

### .zzc.config.json  

For controlling compilation.  
```jsonc
//	The comments are just for clarity. Don't use comments in your config!
{
	"paths": {
		"zzc": "src", //	root for .zzc and generated .zzh files
		"tmp": "tmp", //	destination for .tmp.? files
		"cpp": "cpp", //	destination for .hpp and .cpp files
		"obj": "obj", //	destination for .o files
		"exe": "build/a.exe" //	target (can also be left out and hardcoded into "compiler"."target" command)
	},
	"compiler": {
		"preprocess": ["gcc", "-E", "-o", {"arg": "out"}, {"arg": "in"}],
		"obj": ["g++", "-c", {"var": "CXX_FLAGS"}, "-o", {"arg": "out"}, {"arg": "in"}],
		"target": ["g++", "-o", {"arg":"out"}, {"arg":"in"}],
		"c++": {
			"preprocess": ["g++", "-E", "-o", {"arg": "out"}, {"arg": "in"}],
		}
	},
	"vars": {
		"CXX_FLAGS": ["-Dfun=", "-Dself=(*this)", "-std=c++23"]
	}
}
```
There is a schema for this in `./zzc-config-schema.json`.  
To use it in VSCode, add this to your settings: `"json.schemas": [{"fileMatch": ["*.zzc.config.json"], "url": "file:///path/to/local/zzc-config-schema.json" or "https://raw.githubusercontent.com/BartolHrg/ZZC/refs/heads/main/zzc-config-schema.json"}]`  

Everything is optional.  

`paths` are paths. If some path doesn't exist, it will be generated. (`var` can't be used here)  

`compiler` are commands for compilation.  
`compiler` can have keys:  
- `preprocess`, `obj`: which are then treated as default values for both C and C++.  
- `c`, `c++`: which can specify any of the above (`preprocess`, `obj`) for that specific language.  
- `target`: final product
- Additionally, `preprocess` and `obj` can themselves be objects (like `"obj": {"c": []}`, which is treated exactly the same as `"c": {"obj": []}`).  

Inside `compiler`, lists can have: strings, objects of form `{"arg":"in|out"}` (for input and output files), and `{"var":"name"}` (for variables defined in `vars`).  

`vars` is for defining variables used in config.  


### Important notes

* You must use `fun` to denote functions (including the main function)  
```c++
fun void f() {}
```
* Functions bodies are not parsed. They go as-is in the appropriate place.  
* There are 4 _sections_ generated:  

  * in the `.hpp` file  
  
    1. `hdr_decl` public declarations  
    2. `hdr_impl` inline implementations  
  * in the `.cpp` file  
  
    3. `src_decl` private declarations  
    4. `src_impl` implementations  
* Global `static`, and anonymous namespace `namespace {...}` stuff is private (it goes in src only).  
* You can use `#pragma region zzc tag1 tag2 ...`.  
  Allowed tags are:  
  * `ide`: should be only visible to the text editor, but will not be in generated files.  
  * `cpp`: should not be preprocessed by ZZC.  
  * `zzc`: should be preprocessed by ZZC. (default)  
  * `hdr`, `src`: synonyms for `hdr_impl`, `src_impl`.  
  * `hdr_decl`, `hdr_impl`, `src_decl`, `src_impl`: put region in corresponding _section_.  
  
  Tags can be combined (e.g. `#pragma region zzc src_decl src_impl`) and nested `#pragma region zzc src_decl \n #pragma region zzc src_impl`.  
  Both of these mean the region will go into both _sections_.  
```c++
#pragma region zzc src_decl
	#include <header_for_src_only>
#pragma endregion zzc //	zzc here is important
#pragma region zzc hdr
	//	I know what, putting a static inline variable in the header file, means
	//	And I will use it responsibly
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
	//	this include will go to the src file
	//	but defines from it will still be visible to ZZC
	#include "a.zzh"
#pragma endregion zzc

//	if zzc didn't see a.zzc, this would most likely be an error, 
//	since ZZC doesn't know how to parse `record`
record R {
	...
};
```
* To include other `.zzc` files, you can either include `.zzc` or `.zzh` file.  
  The only difference is that the `.zzc` file will (wrongly) expose private stuff to IDE (and using them will cause an error during compilation)  

## Features  
* Generate declaration and implementation for global variables, functions, class member functions, class static members.  
* Generate forward declaration for struct/class/union.  
* It supports all (many) C++ keywords and quirks (static, inline, template, concept, requires, noexcept, pure virtual, constexpr, default arguments, ...).  
* Nested classes.  
* You can have a pure virtual method with a definition (not in a template):  
```c++
struct S {
	fun virtual void f() = 0 {
		//	code
	}
}
```

## Planned features  

* Generate only if needed (currently, all files are recompiled every time, even if nothing has changed)  
* Similar to `#pragma region zzc` tags, macros for the same purpose:  
```c++
fun void f() hdr_impl({ 
	printf("This body would go to header file");
});
```
* Better CLI, including a command for cleaning.  
* Maybe `extern "C"` support.  

## Limitations  
Currently, the project is still young, and there may be many bugs.  
There are also some edge cases which are allowed in normal C/C++, but are not here.  

* You must use `fun` to write functions.  
* If you use static members of a template, they either must be inline, or you separate declaration and implementation yourself.  
* You can't write an in-class definition of a pure virtual method (`struct S { fun virtual void f() = 0 `~~`{/*not allowed*/}`~~`};`).  
* Default arguments of a class template are not included in the forward declaration of a class, so they can be only used after definition.  
  (Or you can forward declare yourself with default arguments, and not put them in definition).  
* `extern "C"` is not supported (I forgot, but I'm lazy).  

## PS  

The reason why static and pure virtual with definition are not allowed in templates is simple:  
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
int S<T> :: a = 0; //	Notice S<T>
template <typename T>
void S<T> :: f() {}
template <typename T>
void s<T> :: v() {}
```
