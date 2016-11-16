#!/usr/bin/python2.5
from PldlLibrary import *
from Plan_Library_Graph import *
from Graph_Compiler import *
import sys, os

def main() :
	if len(sys.argv) < 2 :
		print >> sys.stderr, "No input file was specified!"
		sys.exit(1)
	planlib = PldlLibrary( sys.argv[1] )
	planlib.print_description( sys.stdout )	

	graph = Graph( planlib )
	graph.make()
	if "pldl" in planlib.path_to_file :
		dot_filename = planlib.path_to_file.replace( '.pldl', '.dot' )
		ps_filename = planlib.path_to_file.replace( '.pldl', '.ps' )
		png_filename = planlib.path_to_file.replace( '.pldl', '.png' )
		fig_filename = planlib.path_to_file.replace( '.pldl', '.fig' )
		pddl_prefix = planlib.path_to_file.replace( '.pldl', '')
	else :
		dot_filename = planlib.path_to_file + '.dot'
		ps_filename = planlib.path_to_file + '.ps'
		png_filename = planlib.path_to_file + '.png'
		fig_filename = planlib.path_to_file + '.fig'
		pddl_prefix = planlib.path_to_file
	
	outstream = open ( dot_filename, "w" )
	graph.write_graph_description( outstream )
	outstream.close()

	compiler = Graph_Compiler( os.path.basename(planlib.path_to_file).replace( '.pldl', '' ) )
	compiler.max_recursion_depth = 10
	compiler.compile( graph )
	compiler.write()

	os.system( 'dot -Tps %s -o %s'%(dot_filename, ps_filename) )
	os.system( 'dot -Tpng %s -o %s'%(dot_filename, png_filename) )
	os.system( 'dot -Tfig %s -o %s'%(dot_filename, fig_filename) )


if __name__ == '__main__' :
	main()
