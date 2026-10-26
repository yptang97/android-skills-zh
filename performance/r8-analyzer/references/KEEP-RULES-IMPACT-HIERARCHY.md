Keep 规则会阻止 R8 进行优化，下面这些规则按其会在代码库中保留的内容范围排序。

## 1. 包级通配符

以下类型的 keep 规则会阻止 R8 对整个包的所有优化，必须不惜一切代价避免，并且必须细化为只针对某个或某几个具体类。

    -keep class com.example.package.** { *; } - Prevents optimization of all the classess including members in the package and subpackages
    -keep class com.example.package.* { *; } - Prevents optimization of all the classes including members in the package
    -keep class **.package.** { *; } - Prevents optimization of all the classess including members in all the package containing name - package.

受影响的类数量会随包层级变化：包层级越高，受影响的类越多。建议细化 keep 规则

## 2. 取反运算符

避免在 keep 规则中使用取反运算符 !，因为它会意外阻止应用中每个类的优化。因此，如果你有任何带 !运算符的 keep 规则，一定要把它替换为范围更窄、更具体的 keep 规则

    -keep class !com.example.MyClass{*;}

这会保留除这个类之外的整个应用。除这个类之外，其余部分的优化都被禁用。

## 3. 同时保留类与成员的 Keep 规则

使用 -keep 选项并在花括号内带通配符（`*`）的 keep 规则，会强制 R8 按定义原样保留指定的类及其成员。这类 keep 规则会阻止对整个类的任何优化，并保留整个类

    -keep class com.example.MyClass { *; }

## 4. Keepclassmembers

带 -keepclassmembers 选项并在花括号内带通配符（`*`）的 keep 规则，会强制 R8 保留所定义的成员。

    -keepclassmembers class com.example.MyClass { *; }

## 5. 带修饰符的 Keep 规格

- 保留类以及**全部**成员，但使用修饰符来允许特定优化（例如混淆）。保留了相当可观的代码（成员），同时留有一定灵活性。

    -keep,allowobfuscation class com.example.MyClass { *; }
    -keep,allowshrinking class com.example.MyClass { *; }

### 6. 指定方法但未带修饰符

保留类与方法，但不启用任何优化

    -keep class com.example.MyClass { void myMethod(); }

## 7. 仅保留类名

只保留类名。未被使用的方法和字段会被 R8 移除。

    -keep class com.example.MyClass

## 8. 不带成员规格的修饰符

通过修饰符保留类的入口点，但规则本身并不表示具体的成员保留逻辑

    -keep,allowobfuscation class com.example.MyClass
    -keep,allowshrinking class com.example.MyClass
    -keep,allowaccessmodification class com.example.MyClass

## 9. 条件式 Keep 规则

仅在满足特定条件时才触发（例如存在类成员时）。这些是范围最窄、最有利于优化的规则。

    -keepclassmembers class com.example.MyClass { <fields>; }
    -keepclasseswithmembers class * { native <methods>; }
