from PldlLibrary import *
from Pldl_And_Or_Graph import *
import os

def make_tabs( n ) :
	return ''.join( [ '\t' for i in range(0,n) ] )

class STRIPS_Action :
	
	def __init__(self) :
		self.name = None
		self.precs = []
		self.adds = []
		self.dels = []
		self.cost = 0

class Plan_Library_To_STRIPS_Compiler :
	
	def __init__(self) :
		self.goals = []
		self.nfluents = 0
		self.fluents = dict()		# fluent string to integer
		self.inv_fluents = dict()	# integer to fluent string
		self.actions = []
		self.domain_name = None
		self.obs_goals = 0
		self.explain_fluents = []
		self.available_fluents = []
		self.uncommitted_fluents = []
		self.ended_fluents = []
		self.explain_actions = 0
		self.completed_fluents = []
		self.parsing = False
		self.parsing_achievers = dict()
		self.parsing_goals = []
		self.in_program_mode = True

	def __get_fluent( self, signature ) :
		try :
			fluent_id = self.fluents[signature]
		except KeyError :
			if 'explained' in signature :
				self.obs_goals += 1
				self.explain_fluents.append(signature)
			if 'completed' in signature :
				self.completed_fluents.append(signature)
			if 'available' in signature :
				self.available_fluents.append(signature)
			if 'uncommitted' in signature :
				self.uncommitted_fluents.append(signature)
			if 'parsed' in signature :
				self.parsing_goals.append(signature)
			if 'control-at-root' in signature :
				self.root_control_fluent = signature
			self.nfluents += 1
			fluent_id = self.nfluents
			self.fluents[signature] = fluent_id
			self.inv_fluents[fluent_id] = signature
		return fluent_id

	def make_control_at_root( self ) :
		signature = "(control-at-root)"
		return self.__get_fluent( signature )

	def make_executed( self, n ) :
		signature = "(executed-%s-node-%s)"%(n.object.name, n.node_id)
		return self.__get_fluent( signature )

	def make_control_at( self, n ) :
		signature = "(control-at-%s-node-%s)"%(n.object.name, n.node_id)
		return self.__get_fluent( signature )

	def make_uncommitted_for( self, object, id ) :
		signature = "(uncommitted-%s-node-%s)"%(object.name,id)
		return self.__get_fluent( signature )

	def make_available_for( self, object, id ) :
		signature = "(available-%s-node-%s)"%(object.name,id)
		return self.__get_fluent( signature )
	
	def make_explained_for( self, object, rep_index ) :
		signature = "(explained-execution-of-%s-%d)"%(object,rep_index)
		return self.__get_fluent( signature )

	def make_parsed_for( self, name, index ) :
		signature = "(parsed-%s-%d)"%(name, index)
		return self.__get_fluent(signature)

	def make_completed_for( self, object, id ) :
		signature = "(completed-%s-node-%s)"%(object.name, id)
		return self.__get_fluent(signature)

	def make_started_for( self, object, id ) :
		signature = "(started-%s-node-%s)"%(object.name,id)
		return self.__get_fluent( signature )

	def make_ended_for( self, object, id ) :
		signature = "(ended-%s-node-%s)"%(object.name,id)
		return self.__get_fluent( signature )

	def make_parse_action( self, taskname, previous ) :
		q = self.make_parsed_for( taskname )
		for p in self.parsing_achievers[taskname] :
			if previous is not None :
				precs = [p, self.make_parsed_for( previous.task_name ) ]
			else :
				precs = [p]
			adds = [q]
			dels = []
			self.make_action( "parse-%s"%taskname, precs, adds, dels, 0 )
		self.parsing_goals.append(q)

	def make_explain_action( self, object, precs, adds, dels = [] ) :
		self.make_action( "explain_obs-execute-%s"%object.name, precs, adds, dels, 0 )
		self.explain_actions += 1

	def make_action( self, name, precs, adds, dels, cost ) :
		a = STRIPS_Action()
		a.name = name
		a.precs = precs
		a.adds = adds
		a.dels = dels
		a.cost = cost
		self.actions.append(a)

	def make_root_call_action( self, n, precs, adds, dels = [] ) :
		try :
			self.make_action( "root-call-%s"%n.object.name, precs, adds, dels, n.weight )
		except :
			self.make_action( "root-call-%s"%n.object.name, precs, adds, dels, 0 )
	
	def make_end_root_call_action( self, n, precs, adds, dels = [] ) :
		self.make_action( "end_root-call-%s"%n.object.name, precs, adds, dels, 0 )

	def make_call_action( self, caller, callee, precs, adds, dels = [] ) :
		try :
			self.make_action( "call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, callee.weight )
		except :
			self.make_action( "call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, 0 )

	def make_end_call_action( self, caller, callee, precs, adds, dels = [] ) :
		self.make_action( "end-call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, 0 )

	def make_explain_call_terminal( self, caller, callee, precs, adds, dels = [] ) :
		try :
			self.make_action( "explain_obs-terminal-call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, callee.weight )
		except :
			self.make_action( "explain_obs-terminal-call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, 0 )
		self.explain_actions += 1


	def make_call_terminal_action( self, caller, callee, precs, adds, dels = [] ) :
		try :
			self.make_action( "terminal-call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, callee.weight )
		except :
			self.make_action( "terminal-call-%s-%s"%(caller.object.name, callee.object.name), precs, adds, dels, 0 )

	def make_start_action_for_method( self, object, precs, adds, dels = [] ) :
		try :
			self.make_action( "start-method-%s"%object.name, precs, adds, dels, object.weight )
		except AttributeError :
			self.make_action( "start-method-%s"%object.name, precs, adds, dels, 0 )

	def make_end_action_for_method( self, object, precs, adds, dels = [] ) :
		self.make_action( "end-method-%s"%object.name, precs, adds, dels, 0 )

	def make_start_action_for_task( self, object, precs, adds, dels = [], cost = 0 ) :
		self.make_action( "start-task-%s"%object.name, precs, adds, dels, cost )

	def make_end_action_for_task( self, object, precs, adds, dels = [], cost = 0 ) :
		self.make_action( "end-task-%s"%object.name, precs, adds, dels, cost )

	def make_execute_action( self, object, precs, adds, dels = [] ) :
		self.make_action( "execute-%s"%object.name, precs, adds, dels, 0 )

	def compile( self, graph ) :
		self.domain_name = graph.lib.library_name
		for n in graph.roots :
			if not self.in_program_mode :
				g = self.make_ended_for( n.object, n.node_id )
				self.goals.append(g)
			else :
				g = self.make_executed( n )
				self.goals.append(g)
			n.generate_STRIPS_fragment( self )
		print >> sys.stdout, "Compilation of library", self.domain_name, "completed"
		print >> sys.stdout, len(self.goals), "goals in library"
		print >> sys.stdout, len(self.fluents), "fluents,", len(self.actions), "actions"	

	def compile_obs_seq( self, graph, obs_seq, parsing = False) :
		self.parsing = parsing
		if graph.lib.library_name != obs_seq.library_name :
			raise RuntimeError, "Observations refer to lib %s, and provided lib is %s"%(observations.library_name, graph.lib.library_name)
		result = False
		for obs in obs_seq.observations :
			for n in graph.roots :
				if n.generate_STRIPS_fragment_for_obs(self, obs, []):
					result = True
		if not result :
			raise RuntimeError, "Could not match observation of task %s"%obs.task_name

						

		print >> sys.stdout, "Compilation of observation sequence finished"
		print >> sys.stdout, self.obs_goals, "explained(obs) fluents added"
		print >> sys.stdout, self.explain_actions, "explain(obs) actions added"

	def write_domain_file( self, filename ) :
		outstream = open( filename, 'w' )
		print >> outstream, "(define"
		print >> outstream, make_tabs(1), "(domain", self.domain_name, ")"
		print >> outstream, make_tabs(1), "(:requirements :strips :action-costs)"
		print >> outstream, make_tabs(1), "(:predicates"
		self.__write_pddl_predicates( outstream )
		print >> outstream, make_tabs(1), ")"
		print >> outstream, make_tabs(1), "(:functions (total-cost))"	
		for a in self.actions :
			self.__write_pddl_action( a, outstream )
		print >> outstream, ")"
		outstream.close()

	def __write_pddl_predicates( self, outstream ) :
		for pred, _ in self.fluents.iteritems() :
			print >> outstream, make_tabs(2), pred

	def __write_pddl_action( self, a, outstream ) :
		print >> outstream, make_tabs(1), "(:action", a.name
		print >> outstream, make_tabs(2), ":precondition"
		print >> outstream, make_tabs(2), "(and"
		for f in a.precs :	
			print >> outstream, make_tabs(3), self.inv_fluents[f] 
		print >> outstream, make_tabs(2), ")"
		print >> outstream, make_tabs(2), ":effect"
		print >> outstream, make_tabs(2), "(and"
		print >> outstream, make_tabs(3), "(increase (total-cost)", a.cost ,")"
		for f in a.adds :
			print >> outstream, make_tabs(3), self.inv_fluents[f] 
		for f in a.dels :
			print >> outstream, make_tabs(3), "(not", self.inv_fluents[f], ")"
		print >> outstream, make_tabs(2), ")"
		print >> outstream, make_tabs(1), ")"

	def write_problem_file_with_obs( self, filename, g, idx ) :
		outstream = open( filename, 'w' )	
		print >> outstream, "(define"
		print >> outstream, make_tabs(1), "(problem", "%s-goal-%s"%(self.domain_name, idx), ")"
		print >> outstream, make_tabs(1), "(:domain %s)"%self.domain_name
		print >> outstream, make_tabs(1), "(:metric minimize (total-cost))"
		print >> outstream, make_tabs(1), "(:init (= (total-cost) 0)"
		if not self.in_program_mode :
			for f in self.uncommitted_fluents :
				print >> outstream, make_tabs(2), f
			for f in self.available_fluents :
				print >> outstream, make_tabs(2), f
			for f in self.completed_fluents :
				print >> outstream, make_tabs(2), f
		else :
			print >> outstream, make_tabs(2), self.root_control_fluent 
		print >> outstream, make_tabs(1), ")"
		print >> outstream, make_tabs(1), "(:goal (and"
		print >> outstream, make_tabs(2), "%s"%self.inv_fluents[g]
		for e in self.explain_fluents :
			print >> outstream, make_tabs(2), e
		#for f in self.completed_fluents :
		#	print >> outstream, make_tabs(2), f
		#for f in self.ended_fluents :
		#	print >> outstream, make_tabs(2), f
		print >> outstream, make_tabs(1), "))"	
		print >> outstream, ")"
		outstream.close()
	
	def write_problem_file( self, filename, g, idx ) :
		outstream = open( filename, 'w' )
		print >> outstream, "(define"
		print >> outstream, make_tabs(1), "(problem", "%s-goal-%s"%(self.domain_name, idx), ")"
		print >> outstream, make_tabs(1), "(:domain %s)"%self.domain_name
		print >> outstream, make_tabs(1), "(:metric minimize (total-cost))"
		print >> outstream, make_tabs(1), "(:init (= (total-cost) 0)"
		for f in self.uncommitted_fluents :
			print >> outstream, make_tabs(2), f
		for f in self.available_fluents :
			print >> outstream, make_tabs(2), f
		for f in self.completed_fluents :
			print >> outstream, make_tabs(2), f
		print >> outstream, make_tabs(1), ")"
		print >> outstream, make_tabs(1), "(:goal (and"
		for f in self.available_fluents :
			print >> outstream, make_tabs(2), f

		print >> outstream, make_tabs(2), "%s"%self.inv_fluents[g]
		for f in self.completed_fluents :
			print >> outstream, make_tabs(2), f

		print >> outstream, make_tabs(1), "))"	
		print >> outstream, ")"
		outstream.close()

	def write_pddl( self, prefix ) :
		path_tokens = os.path.split(prefix)
		filename = '/'.join( list(path_tokens[:-1]) + ['pl-%s-domain.pddl'%path_tokens[-1]]) 
		self.write_domain_file( filename )
		for i in range(0, len(self.goals)) :
			filename = '/'.join( list(path_tokens[:-1]) + ['pl-%s-goal-%d.pddl'%(path_tokens[-1],i)]) 
			self.write_problem_file( filename, self.goals[i],  i )
