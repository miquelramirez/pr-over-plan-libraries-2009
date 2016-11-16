import sys

def make_tabs( n ) :
	return ''.join( [ '\t' for i in range(0,n) ] )

class STRIPS_Fluent :
	
	def __init__(self ) :
		self.name = None
		self.index = -1
		self.negated = False

class STRIPS_Action :
	
	def __init__( self ) :
		self.name = None
		self.pre = []
		self.adds = []
		self.dels = []
		self.cost = 1

# This class compiles a given AND/OR graph into an
# STRIPS planning problem
class Graph_Compiler :

	def __init__( self, problem_name ) :
		self.problem_name = problem_name
		self.max_recursion_depth = 0
		self.initial_state = [] # a list of fluent indices
		self.goal_state = [] # a list of of fluent indices
		self.fluent_table = dict() # maps fluent indices into fluent object
		self.name_to_index = dict() # maps fluent names into indices
		self.index_count = 0
		self.fluents = [] # a list of fluent objects
		self.actions = [] # a list of action objects
		self.top_0 = None

	def __register_fluent( self, f ) :
		try :
			return self.name_to_index[f.name]
		except KeyError :
			f.index = self.index_count
			self.name_to_index[f.name] = f.index
			self.fluent_table[ f.index ] = f
			self.fluents.append( f )
			self.index_count += 1
			return f.index

	def started( self, n, i, negated = False ) :
		f = STRIPS_Fluent()
		f.negated = negated
		if n.type == "OR" :
			f.name = 'started-task-%s-depth-%d'%(n.object.name,i)
		elif n.type == "AND" :
			f.name = 'started-method-%s-%d'%(n.object.name,i)
		else :
			error_msg = "Unknown node type:", n.type
			raise RuntimeError, error_msg
		if f.negated : f.name = 'not-%s'%f.name
		return self.__register_fluent( f )	

	def finished( self, n, i, negated = False ) :
		f = STRIPS_Fluent()
		f.negated = negated
		if n.type == "OR" :
			f.name = 'finished-task-%s-depth-%d'%(n.object.name,i)
		elif n.type == "AND" :
			f.name = 'finished-method-%s-depth-%d'%(n.object.name,i)
		else :
			error_msg = "Unknown node type:", n.type
			raise RuntimeError, error_msg
		if f.negated : f.name = 'not-%s'%f.name
		return self.__register_fluent( f )	

	def top( self, i ) :
		f = STRIPS_Fluent()
		f.name = 'top-at-depth-%d'%i
		index = self.__register_fluent( f )	
		if i == 0 : self.top_0 = index
		return index

	def explain( self, obs ) :
		f = STRIPS_Fluent()
		f.name = 'explained-%s-number-%d'%(obs.task_name, obs.repetition_index)
		return self.__register_fluent( f )

	def __make_start_and( self, n ) :
		for i in range(1,self.max_recursion_depth) :	
			no_children_started_precs = [ self.started( np, i+1, True ) for np in n.children ]	
			for np in n.children :
				if len(np.children) == 0 : #Terminal call
					a = STRIPS_Action()
					a.pre = []
					a.pre.append( self.top( i ) )
					a.pre.append( self.started( n, i ) )
					a.pre.append( self.finished( np, i, True ) )
					try :
						depends_precs = [ self.finished( npp, i ) for npp in n.depends[np.object.name] ]
						a.pre += depends_precs
					except KeyError :
						pass
					a.pre += no_children_started_precs
					a.adds = []
					a.adds.append( self.finished( np, i ) )
					a.dels = []
					a.dels.append( self.finished( np, i, True ) )
					a.name = 'method-%s-calls-primitive-task-%s-at-depth-%d'%(n.object.name, np.object.name, i)
					self.actions.append(a)		
				else :
					a = STRIPS_Action()
					a.pre = []
					a.pre.append( self.top( i ) )
					a.pre.append( self.started( n, i ) )
					a.pre.append( self.finished( np, i, True ) )
					try :
						depends_precs = [ self.finished( npp, i) for npp in n.depends[np.object.name] ]
						a.pre += depends_precs
					except KeyError :
						pass
					a.pre += no_children_started_precs
					a.adds = []
					a.adds.append( self.top( i + 1 ) )
					a.adds.append( self.started( np, i + 1 ) )
					a.dels = []
					a.dels.append( self.top( i ) )
					a.dels.append( self.started( np, i + 1, True ) )
					a.name = 'method-%s-calls-task-%s-at-depth-%d'%(n.object.name, np.object.name, i)
					self.actions.append(a)


	def __make_end_and( self, n ) :
		for i in range (1, self.max_recursion_depth) :
			b = STRIPS_Action()
			b.pre = []
			b.pre.append( self.top(i) )
			b.pre.append( self.started( n, i ) )
			b.pre += [ self.finished( np, i ) for np in n.children ]
			b.adds = []
			b.adds.append( self.finished(n, i - 1) )
			b.adds.append( self.started( n, i , True ) )
			b.adds.append( self.top( i - 1) )
			b.adds += [ self.finished( np, i , True ) for np in n.children ]
			b.dels = []
			b.dels.append( self.top( i ) )
			b.dels.append( self.finished( n, i - 1, True ) )
			b.dels.append( self.started( n, i ) )
			b.dels += [ self.finished( np, i ) for np in n.children ]
			b.name = 'ending-call-to-method-%s-at-depth-%d'%(n.object.name, i )
			self.actions.append(b)

	def __make_start_or_internal( self, n ) :
		for i in range( 1, self.max_recursion_depth ) :
			no_children_started_precs = [ self.started( np, i + 1, True ) for np in n.children ]
			no_children_finished = [ self.finished( np, i, True ) for np in n.children ]
			for np in n.children :
				a = STRIPS_Action()
				a.pre = []
				a.pre.append( self.top( i ) )
				a.pre.append( self.started( n, i ) )
				a.pre += no_children_finished
				a.pre += no_children_started_precs
				a.adds = []
				a.adds.append( self.top( i + 1 ) )
				a.adds.append( self.started( np, i + 1 ) )
				a.dels = []
				a.dels.append( self.top( i ) )
				a.dels.append( self.started( np, i + 1, True ) )
				a.name = 'task-%s-calls-method-%s-at-depth-%d'%(n.object.name, np.object.name, i)
				self.actions.append(a)	
	
	def __make_end_or_internal( self, n ) :
		for i in range ( 1, self.max_recursion_depth ) :
			for np in n.children :
				a = STRIPS_Action()
				a.pre = []
				a.pre.append( self.top(i) )
				a.pre.append( self.started( n, i  ) )
				a.pre.append( self.finished( np, i  ) )
				a.adds = []
				a.adds.append( self.finished( n, i - 1) )
				a.adds.append( self.top(i-1) )
				a.adds += [ self.finished( npp, i , True ) for npp in n.children ]
				a.adds.append( self.started( n, i , True ) )
				a.dels = []			
				a.dels.append( self.top(i ) )
				a.dels.append( self.started( n, i  ) )
				a.dels += [ self.finished( npp, i  ) for npp in n.children ]
				a.dels.append( self.finished( n, i - 1, True ) )
				a.name = 'ending-call-to-task-%s-at-depth-%d'%(n.object.name, i)
				self.actions.append( a )	


	def __make_start_or_root( self, n ) :
		no_children_started_precs = [ self.started( np, 1, True ) for np in n.children ]
		no_children_finished = [ self.finished( np, 0, True ) for np in n.children ]
		for np in n.children :
			a = STRIPS_Action()
			a.pre = []
			a.pre.append( self.top( 0 ) )
			a.pre += no_children_finished
			a.pre += no_children_started_precs
			a.adds = []
			a.adds.append( self.top( 1 ) )
			a.adds.append( self.started( n, 0 ) )
			a.adds.append( self.started( np, 1 ) )
			a.dels = []
			a.dels.append( self.top( 0 ) )
			a.dels.append( self.started( np, 1, True ) )
			a.dels.append( self.started( n, 0, True ) )
			a.name = 'root-task-%s-calls-method-%s-at-depth-%d'%(n.object.name, np.object.name, 0)
			self.actions.append(a)	

	def __make_end_or_root( self, n ) :
		for np in n.children :
			a = STRIPS_Action()
			a.pre = []
			a.pre.append( self.top(0) )
			a.pre.append( self.started( n, 0 ) )
			a.pre.append( self.finished( np, 0 ) )
			a.adds = []
			a.adds.append( self.finished( n, 0 ) )
			a.adds.append( self.started( np, 1, True ) )
			a.adds += [ self.finished( npp, 1, True ) for npp in n.children ]
			a.dels = []			
			a.dels.append( self.started( np, 1 ) )
			a.dels += [ self.finished( npp, 1 ) for npp in n.children ]
			a.dels.append( self.finished( n, 0, True ) )
			a.name = 'ending-call-to-root-task-%s'%n.object.name
			self.actions.append( a )	

	def __process_and_node( self, n ) :
		print >> sys.stdout, "Creating actions for AND node", n.object.name
		self.__make_start_and( n )
		self.__make_end_and( n )		

	def __process_or_node( self, n ) :
		print >> sys.stdout, "Creating actions for OR node", n.object.name
		if len(n.parents) == 0 :
			self.__make_start_or_root( n )
			self.__make_end_or_root( n )
		else :
			if len(n.children) > 0 :
				self.__make_start_or_internal( n )
				self.__make_end_or_internal( n )

	def __process( self, n ) :
		if n.type == 'AND' : self.__process_and_node( n )
		elif n.type == 'OR' : self.__process_or_node( n )
		else :
			error_str = "Unknown node type found:", n.type
			raise RuntimeError, error_str

	def compile( self, graph ) :
		for n in graph.nodes :
			self.__process( n )
		print >> sys.stdout, len(self.actions), "actions in the STRIPS encoding"
		self.__make_initial_state( graph )
		self.__make_goal_state( graph )

	def compile_obs( self, graph, obs_sequence ) :
		
		for o in obs_sequence :
			covered = False
			for n in graph.or_nodes :
				if n.object.name == o.task_name :
					self.__process_obs( n, o ) 
					covered = True
					self.goal_state.append( self.explain( o ) )
					break
			if not covered : 
				print >> sys.stdout, o.task_name, "was not covered!"
				return False	
		return True

	def __process_obs( self, np, obs ) :
		for i in range ( 1, self.max_recursion_depth ) :
			for n in np.parents :
				a = STRIPS_Action()
				a.pre = []
				a.pre.append( self.top( i ) )
				a.pre.append( self.started( n, i ) )
				a.pre.append( self.finished( np, i, True ) )
				if obs.prev_obs != None :
					a.pre.append( self.explain( obs.prev_obs ) )
				try :
					depends_precs = [ self.finished( npp, i ) for npp in n.depends[np.object.name] ]
					a.pre += depends_precs
				except KeyError :
					pass
				a.pre += [ self.started( np, i+1, True ) for np in n.children ]
				a.adds = []
				a.adds.append( self.finished( np, i ) )
				a.adds.append( self.explain( obs ) )
				a.dels = []
				a.dels.append( self.finished( np, i, True ) )
				a.name = 'method-%s-calls-primitive-task-%s-at-depth-%d-justifying-obs'%(n.object.name, np.object.name, i)
				self.actions.append(a)			

	def __make_initial_state( self, graph ) :
		self.initial_state.append( self.top(0) )
		for f in self.fluents :
			if f.negated :
				self.initial_state.append( f.index )

	def __make_goal_state( self, graph ) :
		self.goal_state = [ self.finished( graph.root, 0 ) ]
	
	def __write_domain( self ) :
		outstream = open( self.pddl_domain_name, 'w' )
		print >> outstream, "(define"
		print >> outstream, make_tabs(1), "(domain", self.problem_name, ")"
		print >> outstream, make_tabs(1), "(:requirements :strips )" # we'll be doing classical planning:action-costs)"
		print >> outstream, make_tabs(1), "(:predicates"

		for f in self.fluents :
			print >> outstream, make_tabs(2), "(%s)"%f.name

		print >> outstream, make_tabs(1), ")"
		#print >> outstream, make_tabs(1), "(:functions (total-cost))"	
		for a in self.actions :
			self.__write_pddl_action( a, outstream )
		print >> outstream, ")"
		outstream.close()

	def __write_pddl_action( self, a, outstream ) :
		print >> outstream, make_tabs(1), "(:action", a.name
		print >> outstream, make_tabs(2), ":precondition"
		print >> outstream, make_tabs(2), "(and"
		for f in a.pre :	
			print >> outstream, make_tabs(3), "(%s)"%self.fluent_table[f].name
		print >> outstream, make_tabs(2), ")"
		print >> outstream, make_tabs(2), ":effect"
		print >> outstream, make_tabs(2), "(and"
		#print >> outstream, make_tabs(3), "(increase (total-cost)", a.cost ,")"
		for f in a.adds :
			print >> outstream, make_tabs(3), "(%s)"%self.fluent_table[f].name
		for f in a.dels :
			print >> outstream, make_tabs(3), "(not ", "(%s)"%self.fluent_table[f].name, ")"
		print >> outstream, make_tabs(2), ")"
		print >> outstream, make_tabs(1), ")"
		

	def __write_problem( self ) :
		outstream = open( self.pddl_problem_name, 'w' )	
		print >> outstream, "(define"
		print >> outstream, make_tabs(1), "(problem", "%s-facts"%(self.problem_name), ")"
		print >> outstream, make_tabs(1), "(:domain %s)"%self.problem_name
		#print >> outstream, make_tabs(1), "(:metric minimize (total-cost))"
		print >> outstream, make_tabs(1), "(:init "
		# print >> outstream, make_tabs(2), "(= (total-cost) 0)"
		for i in self.initial_state :
			fluent = self.fluent_table[i]
			print >> outstream, make_tabs(2), "(%s)"%fluent.name
		print >> outstream, make_tabs(1), ")"
		print >> outstream, make_tabs(1), "(:goal (and"
		for i in self.goal_state :
			fluent = self.fluent_table[i]
			print >> outstream, make_tabs(2), "(%s)"%fluent.name
		print >> outstream, make_tabs(1), "))"	
		print >> outstream, ")"
		outstream.close()


	def write( self ) :
		# make names
		self.pddl_domain_name = '%s-domain.pddl'%self.problem_name
		self.pddl_problem_name = '%s-problem.pddl'%self.problem_name
		print >> sys.stdout, "PDDL domain filename:", self.pddl_domain_name
		print >> sys.stdout, "PDDL problem filename:", self.pddl_problem_name
		self.__write_domain()
		self.__write_problem()
