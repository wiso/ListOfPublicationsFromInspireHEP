#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
import re
import argparse
import sqlite3
import difflib
from typing import Optional, List, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

import bibtexparser

print_lock = threading.Lock()


class DataBase:
    """A simple database to store the original and final strings"""

    def __init__(self, filename: str):
        self.filename = filename
        self._con = sqlite3.connect(filename, check_same_thread=False)
        self._cur = self._con.cursor()
        self._cur.execute("CREATE TABLE IF NOT EXISTS entries(key, original, final)")
        self._lock = threading.Lock()
        self._nupdates = 0
        self.substitutions: List[Tuple[str, str]] = []

    def update(self, key: str, original: str, final: str):
        with self._lock:
            self._cur.execute(
                "INSERT INTO entries VALUES (?, ?, ?)",
                (key, original.strip(), final.strip()),
            )
            self._nupdates += 1
            if self._nupdates % 20 == 0:
                self._con.commit()
            if original != final:
                self.substitutions.append((original, final))

    def query(self, original: str):
        try:
            query = "SELECT * FROM entries WHERE original=?"
            with self._lock:
                res = self._cur.execute(query, (original,))
                r = res.fetchone()
        except sqlite3.OperationalError as ex:
            print(f"problem executing query {query} with {original}")
            print("error: %s" % ex)
            raise ex
        if r:
            proposed = r[2]
            if original != proposed:
                with self._lock:
                    self.substitutions.append((original, proposed))
            return proposed
        return None

    def commit(self):
        with self._lock:
            self._con.commit()

    def __del__(self):
        print("closing database")
        self._con.commit()
        self._con.close()


def diff_strings(a: str, b: str) -> str:
    output = []
    matcher = difflib.SequenceMatcher(None, a, b)
    green = "\x1b[38;5;16;48;5;2m"
    red = "\x1b[38;5;16;48;5;1m"
    endgreen = "\x1b[0m"
    endred = "\x1b[0m"

    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            output.append(a[a0:a1])
        elif opcode == "insert":
            output.append(f"{green}{b[b0:b1]}{endgreen}")
        elif opcode == "delete":
            output.append(f"{red}{a[a0:a1]}{endred}")
        elif opcode == "replace":
            output.append(f"{green}{b[b0:b1]}{endgreen}")
            output.append(f"{red}{a[a0:a1]}{endred}")
    return "".join(output)


regex_unicode = re.compile("[^\x00-\x7F]")


def help_unicode(item: str) -> Optional[str]:
    m = regex_unicode.search(item)
    if m:
        return (
            item[: m.start()]
            + "***UNICODE****"
            + item[m.start() : m.end()]
            + "*****UNICODE******"
            + item[m.end() :]
        )
    return None


def replace_unicode(item: str) -> str:
    """Replace unicode characters with their latex equivalent."""
    chars = {
        "\xa0": " ",
        "\u202f": "",
        "\u2009\u2009": " ",
        "−": "-",
        "∗": "*",
        "Λ": r"\Lambda",
    }

    def replace_chars(match):
        char = match.group(0)
        with print_lock:
            print('unicode found, replacing "%s" with "%s"' % (char, chars[char]))
        return chars[char]

    return re.sub("(" + "|".join(list(chars.keys())) + ")", replace_chars, item)


def find_error_latex(filename: str) -> str:
    """Find the error in the log file"""
    log = open(filename, "r", encoding="utf-8").read()
    splitted = log.split("\n")
    for iline, line in enumerate(splitted):
        if (
            "error" in line.lower()
            or "! undefined control sequence." in line.lower()
            or "! missing" in line.lower()
        ):
            break
    else:
        return f"cannot find error in log file {filename}"

    return "\n    ".join(splitted[iline - 3 : iline + 3])


def modify_item(item: str, error: str) -> str:
    editor_command = os.environ.get("EDITOR")
    if not editor_command:
        print("you haven't defined a default EDITOR, (e.g. export EDITOR=emacs)")
        editor_command = input(
            "enter the command to open an editor (e.g. emacs/atom -w/...): "
        )
        os.environ["EDITOR"] = editor_command
    editor_command = editor_command.strip()

    tmp_filename = next(tempfile._get_candidate_names())

    with open(tmp_filename, "w", encoding="utf-8") as f:
        preamble = "do not delete these lines\n" + "error found:\n"
        preamble += error
        r = help_unicode(item)
        if r is not None:
            preamble += r
        preamble += "\ndo not delete these lines"

        for line in preamble.split("\n"):
            f.write("% " + line + " %\n")

        f.write(item)
    subprocess.call([editor_command] + [tmp_filename])
    new_item = open(tmp_filename, encoding="utf-8").read()
    new_item = "\n".join(
        [line for line in new_item.split("\n") if not line.startswith("%")]
    )
    os.remove(tmp_filename)
    return new_item


def check_latex_entry(key: str, tex: str, use_bibtex: bool = False) -> Optional[str]:
    """Check if the entry is valid latex"""

    latex_template_biblatex = r"""
\documentclass{article}
\usepackage[backend=bibtex, style=numeric-comp, sorting=none,
            firstinits=true, defernumbers=true]{biblatex}
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

    latex_template_bibtex = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage[utf8]{inputenc}
\usepackage{syntonly}
\syntaxonly
\begin{document}
Try to cite: \cite{CITATION}.
\bibliographystyle{unsrt}
\bibliography{tmp}
\end{document}
    """

    latex_template = latex_template_bibtex if use_bibtex else latex_template_biblatex
    with tempfile.TemporaryDirectory() as tmpdirname:
        open(os.path.join(tmpdirname, "tmp.bib"), "w", encoding="utf-8").write(tex)
        open(os.path.join(tmpdirname, "tmp.tex"), "w", encoding="utf-8").write(
            latex_template.replace("CITATION", key)
        )

        error = None
        stdout_fn = os.path.join(tmpdirname, "stdout.temp")
        stdout = open(stdout_fn, "w+")

        try:
            subprocess.check_call(
                ["pdflatex", "-interaction=nonstopmode", "tmp.tex"],
                stdout=stdout,
                cwd=tmpdirname,
            )
            subprocess.check_call(["bibtex", "tmp"], cwd=tmpdirname, stdout=stdout)
            subprocess.check_call(
                ["pdflatex", "-interaction=nonstopmode", "tmp.tex"],
                stdout=stdout,
                cwd=tmpdirname,
            )
            subprocess.check_call(
                ["pdflatex", "-interaction=nonstopmode", "tmp.tex"],
                stdout=stdout,
                cwd=tmpdirname,
            )
        except subprocess.CalledProcessError:
            stdout.flush()
            error = find_error_latex(stdout_fn)

        return error


global_counter = 0


def run_entry(entry, nentries, db, fix_unicode):
    with print_lock:
        global global_counter
        global_counter += 1
        print(f"checking {entry.key} {global_counter}/{nentries}")
    raw_original = entry.raw.strip()
    raw_proposed = raw_original

    from_cache = db.query(raw_original)
    if from_cache is not None:
        return

    if fix_unicode:
        raw_proposed = replace_unicode(raw_original)
        if raw_proposed != raw_original:
            with print_lock:
                print(f"unicode found in {entry.key}, fixing")

    while True:
        error = check_latex_entry(entry.key, raw_proposed, args.use_bibtex)
        if error is None:
            break

        with print_lock:
            print(f"problem running item {entry.key}")
            raw_proposed = modify_item(raw_proposed, error).strip()

    if raw_original != raw_proposed:
        with print_lock:
            print(diff_strings(raw_original, raw_proposed))
    db.update(entry.key, raw_original, raw_proposed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check LaTeX bibliography",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: check_biblio bibtex_2016-02-07.bib",
    )
    parser.add_argument("bibtex", default="https://inspirehep.net/")
    parser.add_argument("--fix-unicode", action="store_true")
    parser.add_argument("--nthreads", type=int, default=5)
    parser.add_argument(
        "--use-bibtex", action="store_true", help="use bibtex instead of biblatex"
    )
    args = parser.parse_args()

    try:
        biblio_parsed = bibtexparser.parse_file(args.bibtex)
        db = DataBase("db.sqlite")

        print("found %d comments" % len(biblio_parsed.comments))
        print("found %d strings" % len(biblio_parsed.strings))
        print("found %d preambles" % len(biblio_parsed.preambles))
        print("found %d entries" % len(biblio_parsed.entries))

        nentries = len(biblio_parsed.entries)

        with ThreadPoolExecutor(max_workers=args.nthreads) as p:
            partial_function = functools.partial(
                run_entry, nentries=nentries, db=db, fix_unicode=args.fix_unicode
            )
            futures = {
                p.submit(partial_function, entry): entry.key
                for entry in biblio_parsed.entries
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    future.result()
                except Exception as ex:
                    print(f"problem with entry: {key}")
                    raise ex
                print(f"finished {key}")

    finally:
        biblio = open(args.bibtex, encoding="utf-8").read()
        substitutions = db.substitutions
        print(f"applying {len(substitutions)} substitutions")
        for old, new in substitutions:
            if old == new:
                print("BIG PROBLEM: old == new")
            print(diff_strings(old, new))
            if old not in biblio:
                print("BIG PROBLEM: old not in biblio: %s" % old)
            biblio = biblio.replace(old, new)
        new_biblio_fn = args.bibtex.replace(".bib", "_new.bib")
        with open(new_biblio_fn, "w", encoding="utf-8") as f:
            f.write(biblio)
