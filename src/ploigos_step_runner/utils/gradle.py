"""Shared utils for gradle operations.
"""

import re

from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback
    
class GradleGroovyParserException(Exception):
        """An exception dedicated to gradle's groovy DSL parsing.

        Parameters
        ----------
        file_name : str
            Path to the file that is being parsed.
        message : str, 
            The message detailing the exception.

        Returns
        -------
        Str
            String with the file name and message detailing the exception.
        """
        def __init__(self, file_name, message):
            
            self.file_name = file_name
            self.message = message

        def __str__(self):
            return "%s file: %s" % (self.file_name, self.message)

class GradleGroovyParser:
    """A gradle groovy build file parser. 

    Parameters
    ----------
    file_name : str
        Path to the gradle build file.

    Raises
    ------
    FileNotFoundError
        Unable to find gradle build file.    
    OSError
        Unable to open gradle build file.

    Returns
    -------
    Bool
        True if step completed successfully
        False if step returned an error message
    """    
    file_name = ""
    raw_file = None
    
    def __init__(self, file_name):
        self.file_name = file_name
        with open(file_name) as f:
            self.raw_file = f.read()
    
    def getVersion(self):
        """Gets the project version from a gradle groovy build file.

        Returns
        -------
        str
            Version of the project. If no version is found an empty string is returned.

        Raises
        ------
        GradleGroovyParserException
            If multiple project versions are found in the build file.
        """
        version = ""
        tokens = re.findall("^[ \t]*version[ \t]+[\'\"](.+)[\'\"][ \t]*$(?![^{]*})", self.raw_file, re.MULTILINE)
        if len(tokens) == 1:
            version = tokens[0]
        elif len(tokens) > 1:
            raise GradleGroovyParserException(self.file_name, "More than one version found. " + str(tokens) )   
        return version.strip()

