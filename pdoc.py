import sys
import re
sys.path.append('/usr/local/lib/python3.14/site-packages')
from pdoc.cli import main
import pdoc

sys.argv = ['/usr/local/bin/pdoc3', '--force', '--html', '-o', '.', 'LinearAlgebra']

main()
