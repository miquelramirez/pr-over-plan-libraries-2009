
def is_var( term ) :
	return term[0] == '?'

class Atom :
	def __init__(self) :
		self.predicate = None
		self.terms = None

	def print_to( self, stream ) :
		print >> stream, "( %s )"%" ".join([self.predicate]+self.terms),

class Comparison :
	def __init__(self) :
		self.operator = None
		self.children = []
	
	def print_to( self, stream ) :
		pass

class Negation :
	def __init__(self) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(not",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class And :
	def __init__(self) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(and",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class Or :
	def __init__(self) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(or",
		for c in self.children :
			c.print_to( stream )
		print >> stream, ")",

class Implication :

	def __init__(self) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(imply",
		for c in self.children :
			c.print_to( stream )
		print >> stream, ")",

class ForAll :

	def __init__(self) :
		self.args = []
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(forall",
		print >> stream, "(",
		for x in self.args :
			print >> stream, "%s - %s"%(x.name,x.type.name)
		print >> stream, ")",
		print >> stream, ")",

class Exists :

	def __init__(self) :
		self.args = []
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(exists",
		print >> stream, "(",
		for x in self.args :
			print >> stream, "%s - %s"%(x.name,x.type.name)
		print >> stream, ")",
		print >> stream, ")",

class Unary_Minus :
	
	def __int__( self ) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(-",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",		
	
class Multiply :
	
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(*",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",	

class Add :
	
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(+",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",	

class Substract :
	
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(-",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",	

class Divide :
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(/",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",	

class Greater :
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(>",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",	

class Lesser :
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(<",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",	

class Equal :
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(=",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class Greater_Equal :
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(>=",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class Lesser_Equal :
	def __init__( self ) :
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(>=",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class Assign_Operation :
	
	def __init__(self ) :
		self.operator = None
		self.subject = None
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(%s"%self.operator,
		self.subject.print_to(stream)
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class Numeric_Constant :
	def __init__(self ) :
		self.value = None

	def print_to( self, stream ) :
		print >> stream, self.value,

class Function_Atom :
	
	def __init__( self ) :
		self.symbol = None
		self.terms = []

	def print_to( self, stream ) :
		print >> stream, "(",
		print >> stream, self.symbol,
		for t in self.terms :
			print >> stream, t,
		print >> stream, ")",

class And_Effect :

	def __init__( self ) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "( and",
		for c in self.children :
			c.print_to( stream )
		print >> stream, ")",

class Not_Effect :

	def __init__( self ) :
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "( not",
		for c in self.children :
			c.print_to( stream )
		print >> stream, ")",

class ForAll_Effect :

	def __init__(self) :
		self.args = []
		self.children = []

	def print_to( self, stream ) :
		print >> stream, "(forall",
		print >> stream, "(",
		for x in self.args :
			print >> stream, "%s - %s"%(x.name,x.type.name)
		print >> stream, ")",
		for c in self.children :
			c.print_to(stream)
		print >> stream, ")",

class When_Effect :
	
	def __init__( self ) :
		self.condition = None
		self.children = []
	
	def print_to( self, stream ) :
		print >> stream, "(when",
		self.condition.print_to( stream )
		for c in self.children :
			c.print_to( stream )
		print >> stream, ")",

