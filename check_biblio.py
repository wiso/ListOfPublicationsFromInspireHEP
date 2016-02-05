import os
from io import open
import subprocess
import re


def modify_item(item):
    editor_command = os.environ.get("EDITOR")
    if not editor_command:
        print "you haven't defined a default EDITOR, (e.g. export EDITOR=emacs)"
        editor_command = raw_input("enter the command to open an editor (e.g. emacs/atom/...): ")
        os.environ['editor'] = editor_command
    editor_command = editor_command.strip()

    with open('correction.txt', 'w') as f:
        f.write(item)
    subprocess.call([editor_command, 'correction.txt'])
    with open('correction.txt') as f:
        new_item = f.read()
    return new_item


f = open('bibtex.bib')
biblio = f.read()

regex_key = re.compile(r'@[a-z]+\{([A-Za-z0-9:]+),')

latex_template = r"""
\documentclass{article}
\usepackage[backend=bibtex, style=numeric-comp, sorting=none, firstinits=true, defernumbers=true]{biblatex}
\usepackage{amsmath}
\addbibresource{tmp.bib}
\begin{document}
Try to cite: \cite{CITATION}.
\printbibliography
\end{document}
"""

substitutions = []
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

    error = False
    while True:
        try:
            subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'])
            subprocess.check_call(['bibtex', 'tmp'])
            subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'])
            subprocess.check_call(['pdflatex', '-interaction=nonstopmode', 'tmp.tex'])
        except subprocess.CalledProcessError as error:
            print "problem running %s with item %s" % (error.cmd[0], key)
            new_item = modify_item(item)
            with open('tmp.bib', 'w') as f:
                f.write(new_item)
            substitutions.append((item, new_item))
        else:
            print "%s OK"
            break
