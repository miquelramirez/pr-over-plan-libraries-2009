from PldlLibrary import *

class Node :
	current_idx = 0

	# AND/OR graph node
	def __init__(self) :
		self.node_id = "n_%s"%Node.get_new_id()
		self.object = None
		self.parent = []
		self.children = []
		self.depends = []
		self.in_program_mode = True

	def program_mode( self ) :
		self.in_program_mode = True

	def generate_STRIPS_fragment_regular( self, compiler ) :
		raise RuntimeError, "Not implemented"

	def generate_STRIPS_fragment_program( self, compiler ) :
		raise RuntimeError, "Not implemented"

	def generate_STRIPS_fragment( self, compiler ) :
		if self.in_program_mode :
			self.generate_STRIPS_fragment_program( compiler )
		else :
			self.generate_STRIPS_fragment_regular( compiler )

	def generate_STRIPS_fragment_for_obs_program( self, compiler, object, context ) :
		raise RuntimeError, "Not implemented"

	def generate_STRIPS_fragment_for_obs_regular( self, compiler, object, context ) :
		raise RuntimeError, "Not implemented"

	def generate_STRIPS_fragment_for_obs( self, compiler, object, context ) :
		if self.in_program_mode :
			return self.generate_STRIPS_fragment_for_obs_program( compiler, object, context )
		else :
			return self.generate_STRIPS_fragment_for_obs_regular( compiler, object, context )

	def generate_graphviz_fragment( self, outstream ) :
		raise RuntimeError, "Not implemented"

	def get_new_id( cls ) :
		current = cls.current_idx
		cls.current_idx += 1
		return current

	get_new_id = classmethod(get_new_id)

class AND(Node) :
	
	def __init__(self) :
		Node.__init__(self)
		#self.weight = 1
		pass

	def make_from_lib_object( cls, object, lib, parent ) :
		n = AND()
		n.object = object
		n.parent = parent
		for t in object.steps :
			c = OR.make_from_lib_object( t, lib, n ) 
			assert c is not None
			n.children.append( c )				
		children_map = dict()
		for child in n.children :
			children_map[child.object.name] = child

		# now arrange dependencies between children
		for child in n.children :
			# check what constraints does this children have
			for constraint in object.constraints :
				if constraint.lhs.name == child.object.name :
					child.depends.append( children_map[constraint.rhs.name] )
		return n	
	
	make_from_lib_object = classmethod(make_from_lib_object)

	def generate_STRIPS_fragment_program( self, compiler ) :
		# call(n',n)
		precs = [ compiler.make_control_at( self.parent ) ]
		adds = [ compiler.make_control_at( self ) ]
		dels = [ compiler.make_control_at( self.parent ) ]
		compiler.make_call_action( self.parent, self, precs, adds, dels )

		# end-call(n',n)
		precs = [ compiler.make_control_at( self ) ]
		adds = [ compiler.make_control_at( self.parent ), compiler.make_executed( self ) ]
		dels = [ compiler.make_control_at( self ) ]
	
		for n in self.children :
			precs.append( compiler.make_executed( n ) )
			dels.append( compiler.make_executed( n ) )
		compiler.make_end_call_action( self.parent, self, precs, adds, dels )

		for n in self.children :
			n.generate_STRIPS_fragment( compiler )


	def generate_STRIPS_fragment_regular( self, compiler, context ) :
		# start(n)
		start_precs = [ compiler.make_started_for(self.parent.object, self.parent.node_id),
				compiler.make_uncommitted_for(self.parent.object, self.parent.node_id) ]
		start_adds = [ compiler.make_started_for(self.object, self.node_id) ]
		start_dels = [ compiler.make_uncommitted_for(self.parent.object, self.parent.node_id) ]
		compiler.make_start_action_for_method(self.object, start_precs, start_adds, start_dels )
		# end(n)
		end_precs = [ compiler.make_started_for(self.object, self.node_id) ]
		for n in self.children :
			end_precs.append( compiler.make_ended_for( n.object, n.node_id ) )
		end_adds = [ compiler.make_ended_for(self.object, self.node_id) ]
		end_dels = [ ]
		compiler.make_end_action_for_method(self.object, end_precs, end_adds, end_dels )
		
		for n in self.children :
			n.generate_STRIPS_fragment_program( compiler, context )

	def generate_STRIPS_fragment_for_obs_program(self, compiler, obs, context ) :
		result = False
		for n in self.children :
			if n.generate_STRIPS_fragment_for_obs( compiler, obs, context ) :
				result = True
		return result

	def generate_STRIPS_fragment_for_obs_regular(self, compiler, obs, context ) :
		result = False
		for n in self.children :
			if n.generate_STRIPS_fragment_for_obs( compiler, obs, context ) :
				result = True
		return result

	def generate_graphviz_fragment( self, outstream ) :
		print >> outstream, self.node_id, '[shape=box,label="%s"];'%self.object.name
		# Parent-to-children
		for n in self.children :
			print >> outstream, self.node_id, "->", n.node_id, ";"
		for n in self.children :
			n.generate_graphviz_fragment( outstream )

class OR(Node) :
	def __init__(self) :
		Node.__init__(self)
		pass

	def make_from_lib_object( cls, object, lib, parent ) :
		n = OR()
		n.parent = parent
		n.object = object
		try:
			for m in lib.implemented_by[object.name] :
				c = AND.make_from_lib_object( m, lib, n )
				if c is not None : n.children.append( c )
		except KeyError : # Primitive task
			pass
		return n
	
	make_from_lib_object = classmethod(make_from_lib_object)

	def generate_STRIPS_fragment_for_obs_program( self, compiler, obs, context ) :
		result = False
		if len(self.children) == 0 :
			# terminal OR-node
			if self.object.name != obs.task_name :
				#print "#%s#"%self.object.name, "!=", "#%s#"%obs.task_name
				return False
			#else :
			#	print "MATCH: #%s#"%self.object.name, "=", "#%s#"%obs.task_name

			result = True
		
			precs = [ compiler.make_control_at( self.parent ) ]
			for n in self.depends :
				precs.append( compiler.make_executed( n ) )
			if obs.prev_obs :
				precs.append( compiler.make_explained_for( obs.prev_obs.task_name, obs.prev_obs.repetition_index ) )
			adds = [ compiler.make_executed( self ), 
				compiler.make_explained_for( obs.task_name, obs.repetition_index ) ]
	
			compiler.make_explain_call_terminal( self.parent, self, precs, adds, [] )

		else :
			for n in self.children :
				if n.generate_STRIPS_fragment_for_obs_program( compiler, obs, context ):
					result = True
		return result

	
	def generate_STRIPS_fragment_for_obs_regular( self, compiler, obs, context ) :
		result = False
		if len(self.children) == 0 :
			# terminal OR-node
			if self.object.name != obs.task_name :
				#print "#%s#"%self.object.name, "!=", "#%s#"%obs.task_name
				return False
			#else :
			#	print "MATCH: #%s#"%self.object.name, "=", "#%s#"%obs.task_name

			result = True
			precs = [ compiler.make_started_for( self.parent.object, self.parent.node_id ),
				compiler.make_available_for(self.object, self.node_id) ]
			for n in self.depends :
				precs.append( compiler.make_ended_for( n.object, n.node_id ) )
			if obs.prev_obs :
				precs.append( compiler.make_explained_for( obs.prev_obs.task_name, obs.prev_obs.repetition_index ) )

			adds = [ compiler.make_ended_for( self.object, self.node_id ) ]
			adds.append( compiler.make_explained_for( obs.task_name, obs.repetition_index ) )
			dels = [ compiler.make_available_for(self.object, self.node_id) ]
			compiler.make_explain_action( self.object, precs, adds, dels )

		else :
			for n in self.children :
				if n.generate_STRIPS_fragment_for_obs( compiler, obs, context ):
					result = True
		return result

	def generate_STRIPS_fragment_program( self, compiler ) :
		if len(self.children) == 0 :
			# terminal OR-Node
			precs = [ compiler.make_control_at( self.parent ) ]
			for n in self.depends :
				precs.append( compiler.make_executed( n ) )
			adds = [ compiler.make_executed( self ) ]
			dels = [  ]
			compiler.make_call_terminal_action( self.parent, self, precs, adds, dels )
		else :
			if self.parent is None :
				# root-call(n)
				precs = [ compiler.make_control_at_root() ]
				adds = [ compiler.make_control_at( self ) ]
				dels = [ compiler.make_control_at_root() ]
				compiler.make_root_call_action( self, precs, adds, dels )

				# end-root-call(n',n)
					
				for n in self.children :
					precs = [ compiler.make_control_at( self ) ]
					adds = [ compiler.make_executed( self ) ]
					dels = [ compiler.make_control_at( self ) ]
					precs.append( compiler.make_executed( n ) )
					dels.append( compiler.make_executed( n ) )
					compiler.make_end_root_call_action( self, precs, adds, dels )
			else :
				# call(n', n)
				precs = [ compiler.make_control_at(self.parent) ]
				for n in self.depends :
					precs.append( compiler.make_executed( n ) )
				adds = [ compiler.make_control_at( self ) ]
				dels = [ compiler.make_control_at(self.parent) ]
				compiler.make_call_action( self.parent, self, precs, adds, dels )

				# end-call(n',n)
	
				for n in self.children :
					precs = [ compiler.make_control_at( self ) ]
					precs.append( compiler.make_executed( n ) )
					adds = [ compiler.make_executed( self ), compiler.make_control_at( self.parent ) ]
					dels = [ compiler.make_control_at( self ) ]
					dels.append( compiler.make_executed( n ) )
					compiler.make_end_call_action( self.parent, self, precs, adds, dels )
				

		for n in self.children :
			n.generate_STRIPS_fragment_program( compiler )


	def generate_STRIPS_fragment_regular( self, compiler, context) :
		if len(self.children) == 0 :
			# terminal OR-Node
			precs = [ compiler.make_started_for( self.parent.object, self.parent.node_id ),
				compiler.make_available_for(self.object, self.node_id) ]
			for n in self.depends :
				precs.append( compiler.make_ended_for( n.object, n.node_id ) )
			adds = [ compiler.make_ended_for( self.object, self.node_id ) ]
			dels = [ compiler.make_available_for(self.object, self.node_id) ]
			compiler.make_execute_action( self.object, precs, adds, dels )
		else :
			if len(context) == 0 : cost = 0
			else : cost = 0
			#start(n)
			start_precs = [ compiler.make_available_for(self.object, self.node_id) ]
			if self.parent :
				start_precs.append( compiler.make_started_for( self.parent.object, self.parent.node_id )  )
			for n in self.depends :
				start_precs.append( compiler.make_ended_for( n.object, n.node_id ) )
			start_adds = [ compiler.make_started_for( self.object, self.node_id ) ]
			start_dels = [ compiler.make_available_for(self.object, self.node_id)  ]
			compiler.make_start_action_for_task( self.object, start_precs, start_adds, start_dels, cost )
			#end(n)
			for n in self.children :
				precs = [ compiler.make_started_for( self.object, self.node_id ) ]
				precs.append( compiler.make_ended_for( n.object, n.node_id ) )
				adds = [ compiler.make_ended_for( self.object, self.node_id )]
				dels = [  ]
				compiler.make_end_action_for_task( self.object, precs, adds, dels, cost )
			for n in self.children :
				n.generate_STRIPS_fragment( compiler, context )

	def generate_graphviz_fragment( self, outstream ) :
		print >> outstream, self.node_id, '[shape=ellipse, label="%s"];'%self.object.name
		# Parent-to-children
		for n in self.children :
			print >> outstream, self.node_id, "->", n.node_id, ";"
		# Dependencies
		for n in self.depends :
			print >> outstream, self.node_id, "->", n.node_id, "[style=dotted];"
		for n in self.children :
			n.generate_graphviz_fragment( outstream )

class Graph :
	# Just a container
	def __init__(self, lib ) :
		self.lib = lib
		self.roots = []
		self.nodes = []

	def make( self ) :
		# Build graph nodes from library
		for t in self.lib.top_level :
			self.roots.append( OR.make_from_lib_object( t, self.lib, None ) ) 

	def write_graph_description( self, outstream ) :
		print >> outstream, "digraph G {"
		for n in self.roots :
			n.generate_graphviz_fragment(outstream)	
		print >> outstream, "}"
