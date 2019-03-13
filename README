
Liberty Format.
(From "Liberty Compiler User Guide" Version O-2018.06)
============================================================
Task 1: Understanding Language Concepts

Information in a liberty is contained in language statements
. The three types of liberty statements are: group object,
simple attribute, and complex attribute. Each statement type
have its own syntax.

------------------------------------------------------------
Basic Syntax Rules

There are the Liberty Compiler syntax rules:
* Names are case-sensitive but no limited in length.
* Each identifier must be unique within its scope.
* Statements can span multiple lines, but each line before
  the last must end with a continuation character (\).

------------------------------------------------------------
Group Statements

A group object is a named collection of statements that
defines a liberty, a cell, a pin, a timing arc, a bus,
and so forth.

This is the syntax of a group statement:
group_type (group_name) :
  ... statements ...
}

------------------------------------------------------------
Attribute Statements

An attribute statement defines the characteristics of a
specific object. Attributes are defined within a group and
can be either simple or complex. The two types of attributes
are distinguished by their syntax. All simple attributes use
the same general syntax. Complex attributes, however, have
different syntactic requirements.

This is the syntax of a simple attribute:
attribute_name : attribute_value

This is the syntax of a complex attribute:
attribute_name (parameter1 [, parameter2, parameter3 ...])
============================================================



How to parser a liberty file.
============================================================
According to the liberty format, we use the following six
kinds of string matching to parse the liberty file.

1. group match.
   group_type (group_name) {
     ... statements ...
   }

2. simple attribute match.
   attribute_name : attribute_value

3. complext attribute match.
   attribute_name (parameter1 [, parameter2, parameter3 ...])

4. values match(special complex attribute match, multi lines).
   values ( \
     ... contents ...
   );

5. table match(special simple attribute match, multi lines).
   table : " ... contents ..., \
     ... contents ..., \
     ... contents ...";

6. comment match.
   /* ... */
============================================================



How to save the liberty file data structure.
============================================================
For a group.
currentGroupDic = {
                   'type'   : <type>,
                   'name'   : <name>,
                   key1     : value1,
                   key2     : value2,
                   key3     : value3,
                   ...
                  }

------------------------------------------------------------
For the whole liberty file.
self.libDic = {
               'type'   : <type>,
               'name'   : <name>,
               key1     : value1,
               key2     : value2,
               key3     : value3,
               ...
               'group'  : [group1Dic, group2Dic, ...],
              }

  'group*Dic' means parallel sub-group data strucutre, it
also has simlar data structure as self.libDic.
============================================================



How to speed up with big liberty file.
============================================================
It will cost a long time to parse a big liberty file, but
specifing cellList can save a lot of time if you only want
to get part cell data of the liberty file.

The normal instantiation is as follows.
myParserLiberty = parserLiberty(libFile)

If you instantiate the calss "parserLiberty" as below.
myParserLiberty = parserLiberty(libFile, cellList=['A', 'B'])

It will generate a new lib file with only cell 'A' and 'B'.
libFile.A_B

libertyParser will parse this new liberty file (always small)
and it can save a lot of time.
============================================================



How to verify the function of libertyParser.
============================================================
Sub-function 'restoreLib' is used to verify the function of
libertyParser, it can convert self.libDic into the same data
structure with the original liberty file.

Below is an example on how to verify the function of
libertyParser.

myLibertyParser = libertyParser(libFile)
myLibertyParser.restoreLib()

Save the output message into file libFile.verify.
Then compare the two files.
  diff libFile libFile.verify

You will find, the comments are missing, some lines may
change position, but the new liberty file have the same data
structure with the original one.
============================================================
