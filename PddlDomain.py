import PddlParser
import PddlLexer
import sys
from PddlFormulae import *
from antlr3 import *
from antlr3.tree import *

class PddlType :
	
	def __init__(self, name ) :
		self.name = name
		self.parents = []
		self.exclusive_subtype = False

	def print_to( self, stream ) :
		
		print >> stream, self.name,
		if len(self.parents) > 0 :
			if self.exclusive_subtype :
				print >> stream, "is either a",
				for i in range(0, len(self.parents)) :
					print >> stream, self.parents[i]
					if i < len(self.parents)-1 :
						print >> stream, "or a",
				print >> stream
			else :
				print >> stream, "is a", self.parents[0]
		else :
			print >> stream

class PddlConstant :

	def __init__( self, name, type ) :
		self.name = name
		self.type = type

	def print_to( self, stream ) :
		print >> stream, self.name, "of type", self.type.name

class PddlFunction :
	
	def __init__( self, name ) :
		self.name = name
		self.args = []
		self.type = 'number'

	def print_to( self, stream ) :
		print >> stream, self.name, "of type", self.type, "with args:"
		for var in self.args :
			print >> stream
			var.print_to(stream)

class PddlVar :

	def __init__( self, name, type ) :
		self.name = name
		self.type = type

	def print_to( self, stream ) :
		print >> stream, self.name, "of type", self.type.name

class PddlPredicate :
	
	def __init__( self, name ) :
		self.name = name
		self.args = []

	def print_to( self, stream ) :
		print >> stream, self.name, 
		print >> stream, "with arity", len(self.args)
		for var in self.args :
			print >> stream
			var.print_to(stream)

class PddlAction :
	
	def __init__( self, name ) :
		self.name = name
		self.args = []
		self.precondition = None
		self.effect = None

	def print_to( self, stream ) :
		print >> stream, self.name, 
		print >> stream, "with arity", len(self.args)
		for var in self.args :
			print >> stream
			var.print_to(stream)
		print >> stream, "precondition:"
		if self.precondition : self.precondition.print_to(stream)
		print >> stream
		print >> stream, "effect:"
		self.effect.print_to(stream)
		print >> stream

class PddlDomain :

	def __init__( self, path_to_file ) :
		self.path_to_file = path_to_file
		self.domain = None
		self.requirements = []
		self.type_table = dict()
		self.predicate_table = dict()
		self.action_table = dict()
		self.function_table = dict()
		self.constant_table = dict()
		self.load()

	def print_description( self, stream ) :
		print >> stream, "Description of domain", self.domain,
		print >> stream, "consists in", len(self.type_table.keys()), "type(s),",
		print >> stream, len(self.predicate_table.keys()), "predicate(s),",
		print >> stream, "and", len(self.action_table.keys()), "action(s),",
		print >> stream, "requiring support of the following features:",
		print >> stream, " and ".join( [ req.replace(':','').capitalize() for req in self.requirements ] )
		print >> stream
		print >> stream, "Types details:"
		for _, type in self.type_table.iteritems() :
			type.print_to( stream )
		print >> stream
		print >> stream, "Functions:"
		for _, func in self.function_table.iteritems() :
			func.print_to( stream )
		print >> stream, "Predicates details:"
		for _, pred in self.predicate_table.iteritems() :
			pred.print_to( stream )
		print >> stream
		print >> stream, "Actions details:"
		for _, act in self.action_table.iteritems() :
			act.print_to( stream )
		

	def load( self ) :
		inputstream = ANTLRFileStream(self.path_to_file)
		lexer = PddlLexer.PddlLexer( inputstream )
		tokens = CommonTokenStream( lexer )
		parser = PddlParser.PddlParser( tokens )
		result = parser.domain()
		root = result.tree

		# start processing the AST obtained by parser
		for i in range( 0, root.getChildCount() ) :
			n = root.getChild(i)
			if n.getType() == PddlLexer.DOMAIN_NAME :
				self.__handle_domain_name( n )
			elif n.getType() == PddlLexer.REQUIREMENTS :
				self.__handle_requirements( n )
			elif n.getType() == PddlLexer.TYPES :
				self.__handle_types( n )
			elif n.getType() == PddlLexer.PREDICATES :
				self.__handle_predicate_set( n )
			elif n.getType() == PddlLexer.FUNCTIONS :
				self.__handle_function_set( n )
			elif n.getType() == PddlLexer.CONSTANTS :
				self.__handle_constant_set( n )	
			elif n.getType() == PddlLexer.ACTION :
				self.__handle_action( n )
		print >> sys.stdout, "Loading of", self.path_to_file, "completed"

	def __handle_domain_name( self, n ) :
		self.domain_name = n.getChild(0).getText()

	def __handle_requirements( self, n ) :
		for i in range( 0, n.getChildCount() ) :
			ni = n.getChild(i)
			if ni.getType() == PddlLexer.REQUIRE_KEY :
				self.requirements.append( ni.getText() )	
		if ':typing' not in self.requirements :
			# add 'object' type for untyped domains
			self.type_table['object'] = PddlType( 'object' )
	
	def __handle_types( self, n ) :
		for i in range(0, n.getChildCount() ) :
			n_i = n.getChild(i)
			type = PddlType( n_i.getText() )
			if n_i.getChildCount() != 0 :
				n_ii = n_i.getChild(0)
				if n_ii.getType() == PddlLexer.EITHER_TYPE :
					type.exclusive_subtype = True
					for j in range(0, n_ii.getChildCount()) :
						n_iii = n_ii.getChild(j)
						type.parents.append(n_iii)
				else :
					type.parents.append( n_ii.getText() )
			self.type_table[ type.name ] = type
		# check for implicitly defined types
		new_types_to_add = []
		for _, type in self.type_table.iteritems() :
			for supertype_name in type.parents :
				try :
					supertype = self.type_table[supertype_name]
				except KeyError :
					new_types_to_add.append( PddlType(supertype_name) )
		for new_type in new_types_to_add :
			self.type_table[ new_type.name ] = new_type
		# if no types parsed, even if :typing is specified add 'object' type
		if len(self.type_table.keys()) == 0 :
			self.type_table['object'] = PddlType( 'object' )

	def __handle_constant_set( self, n ) :
		for i in range(0, n.getChildCount() ) :
			ni = n.getChild(i)
			const_name = ni.getText()
			const_type = self.type_table['object']
			if ni.getChildCount() == 1 :
				try :
					const_type = self.type_table[ni.getChild(0).getText()]
				except KeyError :
					err_msg = "Constant", const_name, "found of undeclared type", ni.getChild(0).getText()
					raise RuntimeError, err_msg
			self.constant_table[ const_name ] = PddlConstant( const_name, const_type )

	def __handle_function_set( self, n ) :
		for i in range(0, n.getChildCount() ) :
			self.__handle_function( n.getChild(i) )

	def __handle_function( self, n ) :
		if n.getType() == PddlLexer.NAME : # function name
			function = PddlFunction( n.getText() )
			# process argument list, if any
			for i in range(0, n.getChildCount() ) :
				ni = n.getChild(i)
				self.__handle_var( ni, function )
			self.function_table[ function.name ] = function
	
	def __handle_predicate_set( self, n ) :
		for i in range(0, n.getChildCount() ) :
			self.__handle_predicate( n.getChild(i) )

	def __handle_predicate( self, n ) :
		predicate = PddlPredicate( n.getText() )
		# process argument list
		for i in range(0, n.getChildCount()) :
			ni = n.getChild(i)
			self.__handle_var( ni, predicate )
		self.predicate_table[ predicate.name ] = predicate

	def __handle_var( self, n, subject ) :
		if n.getChildCount() == 0 : # untyped
			subject.args.append( PddlVar( n.getText(), 'object' ) )
		else :
			varname = n.getText()
			typename = n.getChild(0).getText()
			try : 
				type_obj = self.type_table[typename]
			except KeyError : # Whoops! variable of undefined type found
				err_msg = "ERROR: In predicate %s, variable %s has undefined type %s"%(predicate.name, varname, typename)
				raise RuntimeError, err_msg
			subject.args.append( PddlVar( varname, self.type_table[typename] ) )		

	def __handle_precondition( self, n, subject ) :
		if n.getChildCount() == 1 :
			subject.precondition = self.__handle_formula_node(n.getChild(0), subject)
		elif n.getChildCount() == 0 :
			subject.precondition = None
		
		

	def __handle_atom( self, n, action ) :
		f = Atom()
		pred_node = n.getChild(0)
		terms = []
		for i in range(1, n.getChildCount() ) :
			ni = n.getChild(i)	
			terms += [ ni.getText() ]
		# Now check vars are declared	
		for t in terms :
			if is_var(t) :
				declared = False
				for arg in action.args :
					if arg.name == t :
						declared = True
						break
				if not declared :
					err_msg = "In action", action.name, "precondition, undeclared var", t
					raise RuntimeError, err_msg
		if pred_node.getType() == PddlLexer.EQ_PRED :
			# now we need to create for the concrete types
			# of the terms involved
			typename = 'object'
			for arg in action.args :
				if arg.name == terms[0] :
					typename = arg.type.name
					break
			eq_pred = PddlPredicate( 'equals_%s'%typename )
			eq_pred.args.append( PddlVar( '?x', self.type_table[typename] ) )	
			eq_pred.args.append( PddlVar( '?y', self.type_table[typename] ) )
			self.predicate_table[ eq_pred.name ] = eq_pred
			f.predicate = eq_pred.name
			f.terms = terms
		else :
			try :
				pobj = self.predicate_table[pred_node.getText()]
			except KeyError :
				err_msg = "In action %s precondition, undeclared predicate %s found"%(action.name, pred_node.getText())
				raise RuntimeError, err_msg	
			f.predicate = pobj.name
			f.terms = terms
		return f

		
	
	def __handle_comparison( self, n, action ) :
		op_node = n.getChild(0)
		f = None
		if op_node.getText() == '>' : f = Greater()
		elif op_node.getText() == '>=' : f = GreaterEqual()
		elif op_node.getText() == '<' : f = Lesser()
		elif op_node.getText() == '<=' : f = Lesser_Equal()
		elif op_node.getText() == '=' : f = Equal()
		else : return f

		f.children = [ self.__handle_expr_node(n.getChild(1), action), self.__handle_expr_node(n.getChild(2), action) ] 
		return f

	def __handle_expr_node( self, n, action ) :
		if n.getType() == PddlLexer.BINARY_OP :
			return self.__handle_binary_op( n, action )
		elif n.getType() == PddlLexer.UNARY_MINUS :
			return self.__handle_unary_minus( n, action )
		elif n.getType() == PddlLexer.NUMBER :
			return self.__handle_number( n, action )
		elif n.getType() == PddlLexer.FUNC_HEAD :
			return self.__handle_expr_function( n, action )
	
	def __handle_number( self, n, action ) :
		num = Numeric_Constant()
		num.value = n.getText()
		return num

	def __handle_unary_minus( self, n, action ) :
		uminus = Unary_Minus()
		uminus.children = [ self.__handle_expr_node( n, action ) ]
		return uminus

	def __handle_expr_function( self, n, action ) :
		sym_node = n.getChild(0)
		func = Function_Atom()
		func.symbol = sym_node.getText()
		for i in range( 1, n.getChildCount() ) :
			ni = n.getChild(i)
			func.terms += [ ni.getText() ]	
		return func

	def __handle_binary_op( self, n, action ) :
		op_node = n.getChild(0)
		if op_node.getText() == '+' :
			expr = Add()
			expr.children = [ self.__handle_expr_node( n.getChild(1), action),  
					self.__handle_expr_node( n.getChild(2), action) ]
			return expr
		elif op_node.getText() == '-' :
			expr = Substract()
			expr.children = [ self.__handle_expr_node( n.getChild(1), action),
					self.__handle_expr_node( n.getChild(2), action) ]
			return expr
		elif op_node.getText() == '*' :
			expr = Multiply()
			expr.children = [ self.__handle_expr_node( n.getChild(1), action),
					self.__handle_expr_node( n.getChild(2), action) ]
			return expr
		elif op_node.getText() == '/' :
			expr = Divide()
			expr.children= [ self.__handle_expr_node( n.getChild(1), action),
					self.__handle_expr_node( n.getChild(2), action) ]
			return expr
		

	def __handle_forall( self, n, action ) :
		f = ForAll()
		for i in range(0, n.getChildCount()) :
			ni = n.getChild(i)
			if ni.getType() == PddlLexer.VARIABLE :
				self.__handle_var( ni, f )
			else :
				if i != n.getChildCount()-1 :
					raise RuntimeError, "Trouble!!"
				f.children = [ self.__handle_formula_node( n, action ) ]		
		return f
	
	def __handle_exists( self, n, action ) :
		f = Exists()
		for i in range(0, n.getChildCount()) :
			ni = n.getChild(i)
			if ni.getType() == PddlLexer.VARIABLE :
				self.__handle_var( ni, f )
			else :
				if i != n.getChildCount()-1 :
					raise RuntimeError, "Trouble!!"
				f.children = [ self.__handle_formula_node( n, action ) ]		
		return f
	
	def __handle_and( self, n, action ) :
		f = And()

		for i in range(0, n.getChildCount()) :
			ni = n.getChild(i)
			f.children.append( self.__handle_formula_node(ni, action) )
		
		return f	

	def __handle_or( self, n, action ) :
		
		f = Or()
	
		for i in range(0, n.getChildCount() ) :
			ni = n.getChild(i)
			f.children.append( self.__handle_formula_node( ni, action ) )			

		return f

	def __handle_not( self, n, action ) :
		f = Negation()

		for i in range(0, n.getChildCount() ) :
			ni = n.getChild(i)
			f.children.append( self.__handle_formula_node( ni, action ) )

		return f

	def __handle_imply( self, n, action ) :
		f = Implication()

		for i in range(0, n.getChildCount() ) :
			ni = n.getChild(i)
			f.children.append( self.__handle_formula_node( ni, action ) )

		return f

	def __handle_formula_node( self, n, action ) :
		if n.getType() == PddlLexer.AND_GD :
			return self.__handle_and( n, action )
		elif n.getType() == PddlLexer.OR_GD :
			return self.__handle_or( n, action )
		elif n.getType() == PddlLexer.NOT_GD :
			return self.__handle_not( n, action )
		elif n.getType() == PddlLexer.IMPLY_GD :
			return self.__handle_imply( n, action )
		elif n.getType() == PddlLexer.EXISTS_GD :
			return self.__handle_exists( n, action )
		elif n.getType() == PddlLexer.FORALL_GD :
			return self.__handle_forall( n, action )
		elif n.getType() == PddlLexer.COMPARISON_GD :
			return self.__handle_comparison( n, action )
		elif n.getType() == PddlLexer.PRED_HEAD : # Term
			return self.__handle_atom( n, action )
		else :
			raise RuntimeError, "Whooops! %s"%n.getText()

	def __handle_forall_effect( self, n, action ) :
		f = ForAll_Effect()
		for i in range(0, n.getChildCount()) :
			ni = n.getChild(i)
			if ni.getType() == PddlLexer.VARIABLE :
				self.__handle_var( ni, f )
			else :
				if i != n.getChildCount()-1 :
					raise RuntimeError, "Trouble!!"
				f.children = [ self.__handle_effect_node( n, action ) ]		
		return f
	
	def __handle_when_effect( self, n, action ) :
		f = When_Effect()
		f.condition = self.__handle_formula_node( n.getChild(1) )
		f.children = self.__handle_effect_node( n.getChild(2) )
		return f	
	
	def __handle_and_effect( self, n, action ) :
		f = And_Effect()
		for i in range(0, n.getChildCount()) :
			f.children += [ self.__handle_effect_node( n.getChild(i), action ) ]
		return f

	def __handle_not_effect( self, n, action ) :
		f = Not_Effect()
		for i in range(0, n.getChildCount()) :
			f.children += [ self.__handle_effect_node( n.getChild(i), action) ]
		return f
	
	def __handle_assign_effect( self, n, action ) :
		f = Assign_Operation()

		f.operator = n.getChild(0).getText()
		f.subject = self.__handle_expr_function( n.getChild(1), action )
		f.children = [ self.__handle_expr_node( n.getChild(2), action ) ]	

		return f

	def __handle_effect_node( self, n, action ) :
		if n.getType() == PddlLexer.AND_EFFECT :
			return self.__handle_and_effect(n, action)
		elif n.getType() == PddlLexer.FORALL_EFFECT :
			return self.__handle_forall_effect( n, action )
		elif n.getType() == PddlLexer.WHEN_EFFECT :
			return self.__handle_when_effect( n, action ) 
		elif n.getType() == PddlLexer.NOT_EFFECT :
			return self.__handle_not_effect( n, action )
		elif n.getType() == PddlLexer.PRED_HEAD :
			return self.__handle_atom( n, action )
		elif n.getType() == PddlLexer.ASSIGN_EFFECT :
			return self.__handle_assign_effect( n, action )


	def __handle_effect( self, n, subject ) :
		if n.getChildCount() == 1 :
			subject.effect = self.__handle_effect_node(n.getChild(0), subject)
		elif n.getChildCount() == 0 :
			subject.effect = None


	def __handle_action( self, n ) :
		name_node = n.getChild(0)
		action = PddlAction( name_node.getText() )
		for i in range( 1, n.getChildCount() ) :
			ni = n.getChild(i)
			if ni.getType() == PddlLexer.ACTION_PARAMS_LIST :
				for j in range( 0, ni.getChildCount() ) :
					self.__handle_var( ni.getChild(j), action )
			elif ni.getType() == PddlLexer.PRECONDITION :
				self.__handle_precondition( ni, action )
			elif ni.getType() == PddlLexer.EFFECT :
				self.__handle_effect( ni, action )
		self.action_table[action.name] = action
				
