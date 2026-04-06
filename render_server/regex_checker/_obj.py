import re
from dataclasses import dataclass
from enum import Enum

@dataclass
class CheckDetailsData:
    regex: re.Pattern | None = None # The regex pattern used for checking the string
    matched: bool = False # Whether the regex matched or not

    def __bool__(self):
        return self.matched
    
    def __str__(self):
        text = "Matched" if self.matched else "Not matched"
        
        if self.regex is not None:
            text += f": {self.regex.pattern}"
        
        return text
    
    def __repr__(self):
        return f"Details(regex={repr(self.regex)}, matched={self.matched})"

@dataclass
class LoaderDetailsData:
    loaded: int = 0 # Number of loaded objects
    unusual: int = 0 # Number of unusual objects

    def __int__(self):
        return self.loaded
    
    def __bool__(self):
        return self.unusual == 0
    
    def __str__(self):
        return f"Loaded: {self.loaded}, Errors: {self.unusual}"

    def __repr__(self):
        return f"Details(loaded={self.loaded}, unusual={self.unusual})"

class CheckerMode(Enum):
    SERIES = "series" # All regular expression in the sequence are checked, but if one of the regular expression matches, False is printed immediately
    PARALLEL = "parallel" # Of all the regular expression, if one of the regular expression matches, True is immediately printed