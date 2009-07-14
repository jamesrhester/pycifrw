#
# Add shared library path to sys.path
#
import os, sys
sys.path.append(os.path.join(os.path.split(__file__)[0], sys.platform))
del os
del sys
