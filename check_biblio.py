import os
from io import open
import subprocess
import re

f = open('bibtex.bib')
biblio = f.read()

regex_key = re.compile(r'@[a-z]+\{([A-Za-z0-9:]+),')

latex_template = r"""
\documentclass{article}
\usepackage[backend=bibtex, style=numeric-comp, sorting=none, firstinits=true, defernumbers=true]{biblatex}
\addbibresource{tmp.bib}
\begin{document}
Try to cite: \cite{CITATION}.
\printbibliography
\end{document}
"""

for item in biblio.split("\n\n"):
    if '@' not in item:
        continue
    print item
    tmp_biblio = open('tmp.bib', 'w')
    tmp_biblio.write(item)
    tmp_biblio.close()
    m = regex_key.search(item)
    key = m.group(1)

    latex_file = open('tmp.tex', 'w')
    latex = latex_template.replace('CITATION', key)
    latex_file.write(latex)
    latex_file.close()
    raw_input()
    subprocess.Popen(['pdflatex', 'tmp.tex'])
    raw_input()
    subprocess.Popen(['bibtex', 'tmp'])
    raw_input()
    subprocess.Popen(['pdflatex', 'tmp.tex'])
    raw_input()
    subprocess.Popen(['pdflatex', 'tmp.tex'])
    raw_input()
