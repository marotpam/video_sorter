import ConfigParser

class ConfigParserAdapter:

	_ConfigParser = None

	def __init__( self, config_file ):
		self._ConfigParser = ConfigParser.ConfigParser()
		self._ConfigParser.read( config_file )

	def get( self, section, option ):
		return self._ConfigParser.get( section, option )