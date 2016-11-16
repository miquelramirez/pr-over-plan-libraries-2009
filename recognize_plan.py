#!/usr/bin/python2.5
import sys, glob, re, os
from antlr3 import *
from antlr3.tree import *
from PldlObservations import *
from PR_Tools import *

def main() :

	if len( sys.argv ) < 3 :
		print >> sys.stderr, "Insufficient parameters supplied!"
		print >> sys.stderr, "Usage: ./recognize_plan.py <libraries folder> <observation sequence>"
		sys.exit(1)

	libs_folder = sys.argv[1]
	obs_seq_filename = sys.argv[2]

	# Load observation sequence
	observations = PldlObservationSequence( obs_seq_filename )
	# Obtain libraries from folder
	wildcard = '%s/*.pldl'%libs_folder 	
	libraries = glob.glob( wildcard )
	
	# Show on the screen the libraries found
	print >> sys.stdout, "Libraries found at folder %s:"%libs_folder
	for lib in libraries:
		print >> sys.stdout, "\t", lib

	# For each library build a hypothesis object
	hyps = [ Hypothesis( lib, observations ) for lib in libraries ]

	# Test the hypothesis
	for h in hyps : h.test()
	
	# Write Report
		
	report_filename = os.path.basename(obs_seq_filename).replace( '.pldl', '-report.txt' )
	write_report( hyps, obs_seq_filename, report_filename )

if __name__ == '__main__' :
	main()
