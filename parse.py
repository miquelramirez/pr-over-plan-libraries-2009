#!/usr/bin/python2.5
import sys, glob, re, os
from antlr3 import *
from antlr3.tree import *
from PR_Tools import *
import nltk.grammar

def load_grammar( grammar_filename ) :
	grammar_lines = []
	instream = open( grammar_filename )
	for l in instream :
		grammar_lines.append( l.strip() )
	instream.close()
	try :
		grammar = nltk.grammar.parse_pcfg(grammar_lines)
	except ValueError :
		grammar = nltk.grammar.parse_cfg(grammar_lines)
	return grammar

def load_sentence_tokens( sentence_filename ) :
	instream = open( sentence_filename )
	input = instream.read()
	instream.close()
	input_tokens = input.strip().split()
	return input_tokens

def main() :

	if len( sys.argv ) < 3 :
		print >> sys.stderr, "Insufficient parameters supplied!"
		print >> sys.stderr, "Usage: ./parse.py <grammars folder> <sentence>"
		sys.exit(1)

	grammars_folder = sys.argv[1]
	sentence_filename = sys.argv[2]


	# Obtain libraries from folder
	wildcard = '%s/*.cfg'%grammars_folder
	grammars = glob.glob( wildcard )

	# Show on the screen the libraries found
	print >> sys.stdout, "Grammars found at folder %s:"%grammars_folder
	for cfg in grammars:
		print >> sys.stdout, "\t", cfg

	# For each library build a hypothesis object

	if os.path.isdir( sentence_filename ) :
		sentences = glob.glob( '%s/*.txt'%sentence_filename )
		print >> sys.stdout, "Sentences found at folder %s:"%sentence_filename
		for f in sentences :
			print >> sys.stdout, "\t", f
	else :
		sentences = [ sentence_filename ]

	for filename in sentences :
		sentence = load_sentence_tokens( filename )
		hyps = [ Parsing_Hypothesis( load_grammar(cfg), sentence ) for cfg in grammars ]

		# Test the hypothesis
		for h in hyps : h.test()

		# Write Report
		report_filename = os.path.basename( filename )
		report_filename = report_filename.replace( '.txt', '' )
		report_filename = '%s-report.txt'%report_filename

		write_report( hyps, filename, report_filename )

if __name__ == '__main__' :
	main()
