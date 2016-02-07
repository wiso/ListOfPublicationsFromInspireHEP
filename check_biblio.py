import os
from io import open
import subprocess
import tempfile
import re
from glob import glob

regex_unicode = re.compile('[^\x00-\x7F]')
def help_unicode(item):
    m = regex_unicode.search(item)
    print item[:m.start()] + "***UNICODE****" + item[m.start():m.end()] + "*****UNICODE******" + item[m.end():]


def modify_item(item):
    editor_command = os.environ.get("EDITOR")
    if not editor_command:
        print "you haven't defined a default EDITOR, (e.g. export EDITOR=emacs)"
        editor_command = raw_input("enter the command to open an editor (e.g. emacs/atom/...): ")
        os.environ['EDITOR'] = editor_command
    editor_command = editor_command.strip()

    tmp_filename = next(tempfile._get_candidate_names())

    with open(tmp_filename, 'w') as f:
        f.write(item)
    subprocess.call([editor_command, tmp_filename])
    with open(tmp_filename) as f:
        new_item = f.read()
    os.rm(tmp_filename)
    return new_item

tmp_files = glob('tmp*')
for f in tmp_files:
    os.remove(f)

f = open('bibtex.bib')
biblio = f.read()

regex_key = re.compile(r'@[a-z]+\{([A-Za-z0-9:]+),')

latex_template = r"""
\documentclass{article}
\usepackage[backend=bibtex, style=numeric-comp, sorting=none, firstinits=true, defernumbers=true]{biblatex}
\addbibresource{tmp.bib}
\usepackage{amsmath}
\usepackage[utf8]{inputenc}
\usepackage{syntonly}
\syntaxonly
\begin{document}
Try to cite: \cite{CITATION}.
\printbibliography
\end{document}
"""
try:
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
                help_unicode(item)
                new_item = modify_item(item)
                os.remove('tmp.aux')
                os.remove('tmp.blg')
                os.remove('tmp.bbl')
                with open('tmp.bib', 'w') as f:
                    f.write(new_item)
                substitutions.append((item, new_item))
            else:
                break
finally:
    with open('bibtex.bib') as f:
        biblio = f.read()
    for old, new in substitutions:
        biblio = biblio.replace(old, new)
    with open('bibtex.bib', 'w') as f:
        f.write(biblio)
    print "%d fixes done" % len(substitutions)
