# local errors
class LexTokenError(Exception):
   def __init__(self,value):
       self.value = value
   def __str__(self):
       print 'Lex Token Error: ' + self.value

class LexTokenUnfoundError(Exception):
   def __init__(self,value1,value2):
       import string
       self.lineno = len(string.split(value1[0:value2],'\n'))
       firstval = max(0,value2 - 20)	
       lastval = min(len(value1),value2+20)
       self.value = 'Badly formatted file, line no %d\n' % self.lineno
       self.value = self.value + 'In vicinity of:\n' + value1[firstval:lastval]
   def __str__(self):
       print self.value
