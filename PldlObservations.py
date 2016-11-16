import PldlParser
import PldlLexer
import sys
from antlr3 import *
from antlr3.tree import *

class PldlObservation :

	def __init__( self ) :
		self.task_name = None
		self.repetition_index = 1
		self.prev_obs = None
	
class PldlObservationSequence :

	def __init__( self, path_to_file ) :
		self.path_to_file = path_to_file
		self.sequence_name = None
		self.library_name = None
		self.observations = []
		self.true_goal = None
		if self.path_to_file :
			self.load()

	def make_from_tokens( self, token_list ) :
		for token in token_list :
			obs = PldlObservation()
			obs.task_name = token
			self.observations.append( obs )
		self.__bind_observations()

	def load( self ) :
		inputstream = ANTLRFileStream(self.path_to_file)
		lexer = PldlLexer.PldlLexer( inputstream )
		tokens = CommonTokenStream( lexer )
		parser = PldlParser.PldlParser( tokens )
		result = parser.obsSeq()
		root = result.tree

		#start processing AST returned by parser
		for i in range( 0, root.getChildCount() ) :
			n = root.getChild(i)
			if n.getType() == PldlLexer.OBS_SEQ_NAME :
				self.__handle_obs_seq_name( n )
			if n.getType() == PldlLexer.LIBRARY_NAME :
				self.__handle_library_name( n )
			elif n.getType() == PldlLexer.OBSERVATION_LIST :
				for j in range(0, n.getChildCount()) :
					nj = n.getChild(j)
					assert nj.getType() == PldlLexer.OBSERVATION
					self.__handle_obs( nj )
		print >> sys.stdout, "Parsed observation file", self.path_to_file, "found", len(self.observations), "observations"	
		self.__bind_observations()
	
	def __bind_observations( self ) :
		for i in range(1,len(self.observations)) :
			self.observations[i].prev_obs = self.observations[i-1]
			for j in range(0, i ) :
				if self.observations[j].task_name == self.observations[i].task_name :
					self.observations[i].repetition_index += 1
		

	def __handle_library_name( self, n ) :
		self.library_name = n.getChild(0).getText()

	def __handle_obs_seq_name( self, n ) :
		self.sequence_name = n.getChild(0).getText()



	def __handle_obs( self, n ) :
		obs = PldlObservation()
		assert n.getType() == PldlLexer.OBSERVATION
		obs.task_name = n.getChild(0).getText()
		self.observations.append( obs )
