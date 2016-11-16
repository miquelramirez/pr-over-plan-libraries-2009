import PldlParser
import PldlLexer
import sys
from antlr3 import *
from antlr3.tree import *

class PldlStepRequirement :
	
	def __init__( self ) :
		self.lhs = None
		self.rhs = None

	def print_description( self, stream ) :
		print >> stream, self.lhs.name, "requires", self.rhs.name

class PldlMethod :
	
	def __init__( self ) :
		self.name = None
		self.implements = []
		self.steps = []
		self.constraints = []
		self.valid = True

	def print_description( self, stream ) :
		print >> stream, "Method:", self.name
		print >> stream, "Tasks implemented:"
		for t in self.implements : print >> stream, t.name
		print >> stream, "Consists of tasks:"
		for t in self.steps : print >> stream, t.name
		print >> stream, "Imposes the following constraints:"
		for c in self.constraints : 
			c.print_description( stream )	

class PldlTask :
	
	def __init__( self ) :
		self.name = None
		self.valid = True
		self.primitive = False

	def print_description( self, where ) :
		print >> where, self.name, "(Primitive)"

class PldlLibrary :

	def __init__( self, path_to_file = None ) :
		self.path_to_file = path_to_file
		self.library_name = None
		self.tasks = []
		self.top_level = []
		self.methods = []
		self.implemented_by = dict()
		self.implementing = dict()
		self.used_by = dict()
		if self.path_to_file :
			self.load()
			self.check()

	def __process_production( self, prod ) :
		pass
	
	def make_from_grammar( self, grammar ) :

		production_table = dict()	
	
		for prod in grammar.productions() :
			try :
				production_table[prod.lhs()].append( prod.rhs() )
			except KeyError :
				production_table[prod.lhs()] = [ prod.rhs() ]
		
		non_terminals = production_table.keys()
		terminals = []
		# now look for terminals
		for nt in non_terminals :
			for prod in production_table[nt] :
				for sym in prod :
					try :
						k = production_table[sym]
					except KeyError :
						terminals.append( sym )

		sym_to_task = dict()		
		# now create the tasks		
		for sym in non_terminals :
			new_task = PldlTask()
			new_task.name = 'expand-%s'%sym
			self.tasks.append( new_task )
			sym_to_task[sym] = new_task	

		for sym in terminals :
			new_task = PldlTask()
			new_task.name = 'say-%s'%sym
			self.tasks.append( new_task )
			sym_to_task[sym] = new_task

		# let's now create the methods
		for symbol in non_terminals :
			prod = grammar.productions( lhs = symbol )
			for i in range(0, len(prod) ) :
				m = PldlMethod()
				target = sym_to_task[ prod[i].lhs() ]
				m.name = 'apply-production-%d-of-%s'%(i,prod[i].lhs())
				m.implements = [ target ]
				m.steps = [ sym_to_task[step_sym] for step_sym in prod[i].rhs() ]
				
				for j in range(1,len(prod[i].rhs())) :
					c = PldlStepRequirement()
					c.lhs = sym_to_task[ prod[i].rhs()[j] ]
					c.rhs = sym_to_task[ prod[i].rhs()[j-1] ]
					m.constraints.append( c )			
	
				for t in m.implements :
					try :
						self.implemented_by[t.name].append(m)
					except KeyError :
						self.implemented_by[t.name] = [m]
					try :
						self.implementing[m.name].append( t )
					except KeyError :
						self.implementing[m.name] = [t]
				for t in m.steps :
					try :
						self.used_by[t.name].append(m)
					except KeyError :
						self.used_by[t.name] = [m]
				self.methods.append(m)

		self.top_level.append( sym_to_task[ grammar.start() ] )

	def check( self ) :
		self.__check_top_level_tasks_implemented()
		print >> sys.stdout, "Library checked"


	def __check_top_level_tasks_implemented( self ) :
		for t in self.top_level :
			try : 
				implementers = self.implemented_by[t.name]
			except KeyError :
				raise RuntimeError, "Top-level task %s is not implemented by any method"%t.name

	def load( self ) :
		inputstream = ANTLRFileStream(self.path_to_file)
		lexer = PldlLexer.PldlLexer( inputstream )
		tokens = CommonTokenStream( lexer )
		parser = PldlParser.PldlParser( tokens )
		result = parser.library()
		root = result.tree
		
		#start processing AST returned by parser
		for i in range( 0, root.getChildCount() ) :
			n = root.getChild(i)
			if n.getType() == PldlLexer.LIBRARY_NAME :
				self.__handle_library_name( n )
			elif n.getType() == PldlLexer.TASKS :
				self.__handle_tasks( n, False )
			elif n.getType() == PldlLexer.TOP_LEVEL_TASKS :
				try:
					self.__handle_top_level_tasks( n )
				except RuntimeError, e :
					print >> sys.stderr, "Error processing top-level tasks:"
					print >> sys.stderr, e
					raise RuntimeError, "Semantic Error"
			elif n.getType() == PldlLexer.METHOD :
				self.__handle_method(n)
		print >> sys.stdout, "Loading of", self.path_to_file, "completed"	

	def __handle_library_name( self, n ) :
		self.library_name = n.getChild(0).getText()

	def __handle_tasks( self, n, are_primitives ) :
		for i in range( 0, n.getChildCount() ) :
			n_i = n.getChild(i)
			new_task = PldlTask()
			new_task.name = n_i.getText()
			self.tasks.append( new_task )

	def __handle_top_level_tasks( self, n ) :
		for i in range (0, n.getChildCount() ) :
			n_i = n.getChild(i)
			name = n_i.getText()
			# check whether there is already a task declared with
			# this name
			declared = False
			task = None
			for t in self.tasks :
				if t.name == name :
					declared = True
					task = t
					break
			if not declared :
				raise RuntimeError, "Top-level task %s was not declared"%name
			self.top_level.append( task )	


	def __handle_method( self, n ) :
		m = PldlMethod()
		for i in range( 0, n.getChildCount() ) :
			n_i = n.getChild(i)
			if n_i.getType() == PldlLexer.NAME :
				m.name = n_i.getText()
			elif n_i.getType() == PldlLexer.IMPLEMENTS :
				try:
					self.__extract_task_names( n_i, m.implements )
				except RuntimeError, e:
					print >> sys.stderr, "Problem in :implements of method", m.name
					print >> sys.stderr, str(e)
					raise RuntimeError, "Semantic Error"
			elif n_i.getType() == PldlLexer.STEPS :
				try:
					self.__extract_task_names( n_i, m.steps )
				except RuntimeError, e:
					print >> sys.stderr, "Problem in :steps of method", m.name
					print >> sys.stderr, e
					raise RuntimeError, "Semantic Error"					
			elif n_i.getType() == PldlLexer.CONSTRAINTS :
				try:
					self.__extract_constraints( n_i, m )
				except RuntimeError, e :
					print >> sys.stderr, "Problem in :constraints of method", m.name
					print >> sys.stderr, e
					raise RuntimeError, "Semantic Error"							
		for t in m.implements :
			try :
				self.implemented_by[t.name].append(m)
			except KeyError :
				self.implemented_by[t.name] = [m]
			try :
				self.implementing[m.name].append( t )
			except KeyError :
				self.implementing[m.name] = [t]
			
		for t in m.steps :
			try :
				self.used_by[t.name].append(m)
			except KeyError :
				self.used_by[t.name] = [m]
		self.methods.append(m)

	def __extract_task_names( self, n, task_list ) :
		for i in range( 0, n.getChildCount() ) :
			task_name = n.getChild(i).getText()
			# Check the task has been declared
			declared = False
			task = None
			for t in self.tasks :
				if t.name == task_name :
					declared = True
					task = t
			if not declared :
				raise RuntimeError, "Undeclared task: %s"%task_name
			task_list.append( task )

	def __extract_constraints( self, n, method ) :
		for i in range (0, n.getChildCount()) :
			n_i = n.getChild(i)
			if n_i.getType() == PldlLexer.REQUIRES :
				lhs_name = n_i.getChild(0).getText()
				rhs_name = n_i.getChild(1).getText()
				# Check that constraints are referring to steps of the method
				declared_lhs = False
				declared_rhs = False
				task_lhs = None
				task_rhs = None
				for t in method.steps :
					if t.name == lhs_name :
						declared_lhs = True
						task_lhs = t
					if t.name == rhs_name :
						declared_rhs = True
						task_rhs = t
				if not declared_lhs :
					raise RuntimeError, "Undeclared task: %s"%lhs_name
				if not declared_rhs :
					raise RuntimeError, "Undeclared task: %s"%rhs_name
				req = PldlStepRequirement()
				req.lhs = task_lhs
				req.rhs = task_rhs
				method.constraints.append( req )

	def print_description( self, stream ) :
		print >> stream, "Library:", self.library_name
		print >> stream, "Library specifies", len(self.tasks), "tasks",
		for t in self.tasks :
			t.print_description( stream )
		print >> stream, "Library specifies", len(self.methods), "methods"
		for m in self.methods :
			m.print_description( stream )
