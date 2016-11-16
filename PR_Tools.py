import benchmark, os, re
from PldlLibrary import *
from Plan_Library_Graph import *
from PldlObservations import *
from Graph_Compiler import *

def make_filename( pl_path, obs_path ) :
	pl_path_tokens = os.path.split(pl_path)
	obs_path_tokens = os.path.split(obs_path)
	template = "pr-%s_%s"%( pl_path_tokens[-1].replace('.pldl',''), obs_path_tokens[-1].replace('.pldl','') )
	return template

class LAMA_Planner :
	def __init__( self ) :
		self.max_time = 1800
		self.max_mem = 2048
		self.signal = None
		self.time = None
		self.solvable = True
		self.failure = False
		self.plan = []
		self.fluents = 0
		self.ops = 0
		self.search = 0
		self.result = "lama-result.txt"

	def execute( self, domain, problem ) :
		cmd_string = './solvers/LAMA/lama-driver.sh %s %s %s'%(domain, problem, result)
		self.log = benchmark.Log( problem.replace('.pddl','.log' ) )
		self.signal, self.time = benchmark.run( cmd_string, self.max_time, self.max_mem, self.log )
		self.gather_execution_data()

	def gather_execution_data( self ) :
		pass

class FF_Planner : # A simple interface wrapping the planner, for now FF
	
	def __init__( self ) :
		self.max_time = 600
		self.max_mem = 2048
		self.signal = None
		self.time = None
		self.solvable = True
		self.failure = False
		self.plan = []
		self.fluents = 0
		self.ops = 0
		self.search = 0
		self.sol_method = None

	def execute( self, domain, problem ) :
		cmd_string = 'solvers/metric-ff/ff -o %s -f %s'%(domain, problem)
		self.log = benchmark.Log( problem.replace('.pddl','.log' ) )
		self.signal, self.time = benchmark.run( cmd_string, self.max_time, self.max_mem, self.log )
		self.gather_execution_data()

	def gather_execution_data( self ) :
		print >> sys.stdout, "Code found:", self.signal
		if self.signal != 0 :
			pattern = re.compile( r'goal can be simplified to FALSE' )
			instream = open( self.log.name  )
			simp_to_false_found = False
			for line in instream :
				line = line.strip()
				m = pattern.search( line )
				if m is not None :
					simp_to_false_found = True
					break
			instream.close()
			if simp_to_false_found : self.solvable = False
			else : self.failure = True
			return

		#action_cost_re = re.compile( r'\d+:\s(.+)\s\((\d+\.\d+)\)' ) #for gathering costs
		action_cost_re = re.compile( r'\d+:\s(.+)' )
		fluents_ops_re = re.compile( r'(\d+) facts and (\d+) actions' )
		expanded_re = re.compile( r'evaluating (\d+) states' )
		hc_failed_re = re.compile( r'Enforced Hill-climbing failed' )	

		instream = open( self.log.name  )
		plan_found = False
		for line in instream :
			line = line.strip()
			if "step" == line[0:4] :
				plan_found = True
				print >> sys.stdout, "Matching plan ops..."	
			if not plan_found :
				m = fluents_ops_re.search( line )
				if m is not None :
					self.fluents = int( m.group(1) )
					self.ops = int( m.group(2) )
					continue
				m = expanded_re.search( line )
				if m is not None :
					self.search = int( m.group(1) )
					continue
				m = hc_failed_re.search( line )
				if m is not None :
					self.sol_method = 'BFS'
			else :
				m = action_cost_re.search( line ) 
				if m is None :
					plan_found = False
					continue
				print "Matched action cost pair", m.group()
				action_name = m.group(1)
				action_cost = 1.0 #float(m.group(2))	
				self.plan.append( (action_name, action_cost) )
		
		instream.close()
		if self.sol_method is None :
			self.sol_method = 'EHC'
		print self.plan

class Hypothesis :

	def __init__( self, path_to_lib, observations ) :
		self.library_path = path_to_lib
		self.obs_seq = observations
		self.library = PldlLibrary( self.library_path )
		self.AO_graph = Graph( self.library )
		self.AO_graph.make()	
		self.compiler = Graph_Compiler( make_filename( self.library_path, self.obs_seq.path_to_file ) )
		self.compiler.max_recursion_depth = 10
		self.compiler.compile( self.AO_graph )
		self.rejected = True
		self.time = None
		self.success = False
		self.plan_cost = 'n/a'
		self.planner = FF_Planner()

	def test( self ) :
		all_covered = self.compiler.compile_obs( self.AO_graph, self.obs_seq.observations )
		if not all_covered : # Trivial rejection
			self.time = 0.0
			self.success = True
			return
		self.compiler.write()
		self.planner.execute( self.compiler.pddl_domain_name, self.compiler.pddl_problem_name )
		
		if self.planner.failure : 
			self.success = False	
			self.time = 'n/a'
			self.plan_cost = 'n/a'
			self.rejected = '?'
			self.sol_method = 'None'
		else :
			self.success = True
			self.time = self.planner.time
			self.sol_method = self.planner.sol_method
			if self.planner.solvable : self.rejected = False
			self.plan_cost = 0.0
			for a, c in self.planner.plan :
				self.plan_cost += c

class Parsing_Hypothesis :

	def __init__( self, grammar, sentence ) :
		self.grammar = grammar
		self.library = PldlLibrary( )
		self.library.make_from_grammar( self.grammar )
		self.obs_seq = PldlObservationSequence( None )
		self.obs_seq.make_from_tokens( [ 'say-%s'%token for token in sentence ] )
		self.AO_graph = Graph( self.library )
		self.AO_graph.make()	
		self.compiler = Graph_Compiler( 'pr-grammar' )
		self.compiler.max_recursion_depth = 30
		self.compiler.compile( self.AO_graph )
		self.rejected = True
		self.time = None
		self.success = False
		self.plan_cost = 'n/a'
		self.planner = FF_Planner()

	def test( self ) :
		all_covered = self.compiler.compile_obs( self.AO_graph, self.obs_seq.observations )
		if not all_covered : # Trivial rejection
			print >> sys.stdout, "Not all input tokens were covered by the grammar!"
			self.time = 0.0
			self.success = True
			return
		self.compiler.write()
		self.planner.execute( self.compiler.pddl_domain_name, self.compiler.pddl_problem_name )
		
		if self.planner.failure : 
			self.success = False	
			self.time = 'n/a'
			self.plan_cost = 'n/a'
			self.sol_method = None
			self.rejected = '?'
		else :
			self.success = True
			self.time = self.planner.time
			self.sol_method = self.planner.sol_method
			if self.planner.solvable : self.rejected = False
			self.plan_cost = 0.0
			for a, c in self.planner.plan :
				self.plan_cost += c


def write_report( hyps, input_filename, report_filename ) :
	outstream = open( report_filename, 'w' )

	print >> outstream, 'obs_file="%s"'%input_filename
	
	for i in range(0, len(hyps) ) :
		print >> outstream, 'hyp[%d].name="%s"'%( i, hyps[i].AO_graph.root.object.name )
		print >> outstream, 'hyp[%d].success="%s"'%(i, hyps[i].success )
		print >> outstream, 'hyp[%d].rejected="%s"'%(i, hyps[i].rejected )
		print >> outstream, 'hyp[%d].plan_cost="%s"'%(i, hyps[i].plan_cost )
		print >> outstream, 'hyp[%d].time="%s"'%(i, hyps[i].time )
		print >> outstream, 'hyp[%d].fluents="%s"'%(i, hyps[i].planner.fluents )
		print >> outstream, 'hyp[%d].ops="%s"'%(i, hyps[i].planner.ops )
		print >> outstream, 'hyp[%d].search="%s"'%(i, hyps[i].planner.search )
		print >> outstream, 'hyp[%d].sol_method="%s"'%(i, hyps[i].planner.sol_method )

	outstream.close()

