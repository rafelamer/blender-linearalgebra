import sys
import re
sys.path.append('/usr/local/lib/python3.13/site-packages')
from pdoc.cli import main

sys.argv = ['/usr/local/bin/pdoc3', '--force', '--html', '-o', '.', 'LinearAlgebra']

main()
