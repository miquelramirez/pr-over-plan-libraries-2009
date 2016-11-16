from PldlLibrary import *

class Node :

	def __init__( self ) :
		self.node_id = ""
		self.object = None
		self.parents = []
		self.children = []
		self.depends = []
		self.type = None
		self.obs = None
	
	def generate_STRIPS_fragment( self, compiler ) :
		raise RuntimeError, "Not implemented"

	def generate_graphviz_fragment( self, outstream ) :
		raise RuntimeError, "Not implemented"

class AND( Node ) :
	
	def __init__(self) :
		Node.__init__(self)
		self.type = "AND"

	def make_from_lib( cls, lib, object ) :
		n = AND()
		n.node_id = object.name.replace( '-', '_')
		n.object = object
		n.parents = [ t.name for t in lib.implementing[n.object.name] ]
		n.children = [ t.name for t in object.steps ]
		n.depends = object.constraints
		return n
	
	make_from_lib = classmethod(make_from_lib)

	def replace_names_by_refs( self, graph ) :
		new_parents = []
		for name in self.parents :
			try :
				new_parents.append( graph.name_to_node[name] )
			except KeyError :
				error_str = "Parent %s of AND node %s was not found"%(name, self.object.name)
				raise RuntimeError, error_str
		self.parents = new_parents
		if len(self.parents) == 0 :
			error_msg = "AND node %s has no parents!"%self.object.name
			raise RuntimeError, error_msg
		new_children = []
		for name in self.children :
			try :
				new_children.append( graph.name_to_node[name ] )
			except KeyError :
				error_str = "Children %s of AND node %s was not found"%(name, self.object.name)
		self.children = new_children
		if len(self.children) == 0 :
			error_msg = "AND node %s has no children!"%self.object.name
			raise RuntimeError, error_msg
		new_deps = dict()
		for c in self.depends :
			try :
				new_deps[c.lhs.name].append( graph.name_to_node[c.rhs.name] )
			except KeyError :
				new_deps[c.lhs.name] = [ graph.name_to_node[c.rhs.name] ]
		self.depends = new_deps

	def generate_STRIPS_fragment( self, compiler ) :
		pass

	def generate_graphviz_fragment( self, outstream ) :
		print >> outstream, self.node_id, ' [shape=box,label="%s"];'%self.object.name
		# Parent-to-children
		for n in self.children :
			print >> outstream, self.node_id, "->", n.node_id, ";"

class OR( Node ) :
	
	def __init__(self) :
		Node.__init__(self)
		self.type = "OR"

	def make_from_lib( cls, lib, object ) :
		n = OR()
		n.node_id = object.name.replace( '-', '_')
		n.node_id = n.node_id.replace( ' ', '_' )
		n.object = object
		try :
			n.parents = [ m.name for m in lib.used_by[n.object.name] ]
		except KeyError :
			print >> sys.stdout, "Root node:", n.object.name
		try :
			n.children = [ m.name for m in lib.implemented_by[n.object.name] ]
		except KeyError :
			print >> sys.stdout, "Terminal node:", n.object.name
		return n
	
	make_from_lib = classmethod(make_from_lib)
	
	def replace_names_by_refs( self, graph ) :
		new_parents = []
		for name in self.parents :
			try :
				new_parents.append( graph.name_to_node[name] )
			except KeyError :
				error_str = "Parent %s of AND node %s was not found"%(name, self.object.name)
				raise RuntimeError, error_str
		self.parents = new_parents
		new_children = []
		for name in self.children :
			try :
				new_children.append( graph.name_to_node[name ] )
			except KeyError :
				error_str = "Children %s of AND node %s was not found"%(name, self.object.name)
		self.children = new_children

	def generate_STRIPS_fragment( self, compiler ) :
		pass

	def generate_graphviz_fragment( self, outstream ) :
		print >> outstream,  self.node_id, ' [shape=ellipse, label="%s"];'%self.object.name
		# Parent-to-children
		for n in self.children :
			print >> outstream, self.node_id, "->", n.node_id, ";"

class Graph :

	def __init__( self, lib ) :
		self.lib = lib
		self.root = None
		self.or_nodes = []
		self.and_nodes = []
		self.nodes = []
		self.name_to_node = dict()

	def make( self ) :
		for t in self.lib.tasks :
			n = OR.make_from_lib( self.lib, t ) 
			self.name_to_node[ t.name ] = n
			self.or_nodes.append( n )
			self.nodes.append( n )
			if len(n.children) == 0 : self.root = n
		for m in self.lib.methods :
			n = AND.make_from_lib( self.lib, m )
			self.name_to_node[ m.name ] = n
			self.and_nodes.append( n )
			self.nodes.append( n )
		for n in self.nodes :
			n.replace_names_by_refs( self )

		for n in self.nodes :
			if len(n.parents) == 0 :
				self.root = n
				break

		print >> sys.stdout, "AND/OR Graph for library", self.lib.library_name,
		print >> sys.stdout, "has", len(self.or_nodes), "OR nodes, and ",
		print >> sys.stdout, len(self.and_nodes), "AND nodes"

	def write_graph_description( self, outstream ) :
		print >> outstream, "digraph G {"
		for n in self.nodes :
			n.generate_graphviz_fragment( outstream )
		print >> outstream, "}"
		
