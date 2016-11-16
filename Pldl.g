grammar Pldl;
options {
	output=AST;
	ASTLabelType=CommonTree;
	backtrack=true;
	memoize=true;
	language=Python;
}

tokens {
	LIBRARY;
	LIBRARY_NAME;
	TASKS;
	TOP_LEVEL_TASKS;
	PRIMITIVE_TASKS;
	METHOD;
	IMPLEMENTS;
	STEPS;
	CONSTRAINTS;
	REQUIRES;
	OBS_SEQ_DEF;
	OBS_SEQ_NAME;
	OBSERVATION_LIST;
	OBSERVATION;
}

/* Start of grammar */

pldlDoc : library | obsSeq;

library : '(' 'define' libraryName
	tasksDef?
	topLevelDef?
	methodDef*
	')'
	-> ^(LIBRARY libraryName tasksDef? topLevelDef? methodDef*)
	;

libraryName : '(' 'library' NAME ')'
	-> ^(LIBRARY_NAME NAME)
	;

tasksDef : '(' ':tasks' taskNameList ')'
	-> ^(TASKS taskNameList)
	;

taskNameList : (taskName+)
	;

taskName : NAME;

/*
primitivesDef : '(' ':primitives' taskNameList ')'
	-> ^(PRIMITIVE_TASKS taskNameList)
	;
*/
	 
topLevelDef : '(' ':top' '-' 'level' taskName ')'
	-> ^(TOP_LEVEL_TASKS taskName)
	;

methodDef : '(' ':method' methodName implementsDef stepsDef constraintsDef? ')'
	-> ^(METHOD methodName implementsDef stepsDef constraintsDef?)
	;

methodName : NAME;

implementsDef : ':implements' '(' taskNameList ')'
	-> ^(IMPLEMENTS taskNameList)
	;

stepsDef : ':steps' '(' taskNameList ')'
	-> ^(STEPS taskNameList)
	;

constraintsDef : ':constraints' '(' constraintsList ')'
	-> ^(CONSTRAINTS constraintsList)
	;

constraintsList : (constraint+)
	;

constraint :	requires
	;

requires : '(' 'requires' taskName taskName ')'
	-> ^(REQUIRES taskName taskName)
	;

obsSeq	: '(' 'define' obsSeqName libraryReference observationSeq ')'
	-> ^(OBS_SEQ_DEF obsSeqName libraryReference observationSeq)
	;

libraryReference : '(' ':library' NAME ')'
	-> ^(LIBRARY_NAME NAME)
	;

obsSeqName : '(' 'sequence' NAME ')'
	-> ^(OBS_SEQ_NAME NAME)
	;

observationSeq : '(' ':observed' obsListElem+ ')'
	-> ^(OBSERVATION_LIST obsListElem+)
	;

obsListElem :	'(' taskName ')'
	-> ^(OBSERVATION taskName)
	;

/************* LEXER ****************************/
NAME:    LETTER ANY_CHAR* ;

fragment LETTER:	'a'..'z' | 'A'..'Z';

fragment ANY_CHAR: LETTER | '0'..'9' | '-' | '_';

VARIABLE : '?' LETTER ANY_CHAR* ;

NUMBER : DIGIT+ ('.' DIGIT+)? ;

fragment DIGIT: '0'..'9';

LINE_COMMENT
    : ';' ~('\n'|'\r')* '\r'? '\n' { $channel = HIDDEN; }
    ;

WHITESPACE
    :   (   ' '
        |   '\t'
        |   '\r'
        |   '\n'
        )+
        { $channel = HIDDEN; }
    ;
