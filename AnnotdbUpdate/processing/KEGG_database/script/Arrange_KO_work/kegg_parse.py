#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/22 13:20
# @Author  : U make me wanna surrender my soul
from Bio.KEGG import _default_wrap, _wrap_kegg, _write_kegg

# Set up line wrapping rules (see Bio.KEGG._wrap_kegg)
name_wrap = [0, "", (" ", "$", 1, 1), ("-", "$", 1, 1)]
id_wrap = _default_wrap


class Record:
    """Holds info from a KEGG Gene record.

    Attributes:
     - entry       The entry identifier.
     - name        A list of the gene names.
     - definition  The definition for the gene.
     - orthology   A list of 2-tuples: (orthology id, role)
     - organism    A tuple: (organism id, organism)
     - position    The position for the gene
     - motif       A list of 2-tuples: (database, list of link ids)
     - dblinks     A list of 2-tuples: (database, list of link ids)

    """

    def __init__(self):
        """Initialize new record."""
        self.entry = ""
        self.name = []
        self.definition = ""
        self.orthology = []
        self.organism = ""
        self.position = ""
        self.motif = []
        self.dblinks = []
        self.pathway = []

    def __str__(self):
        """Return a string representation of this Record."""
        return self._entry() + self._name() + self._dblinks() + "///"

    def _entry(self):
        return _write_kegg("ENTRY", [self.entry])

    def _name(self):
        return _write_kegg(
            "NAME", [_wrap_kegg(l, wrap_rule=name_wrap) for l in self.name]
        )

    def _definition(self):
        return _write_kegg("DEFINITION", [self.definition])

    def _dblinks(self):
        s = []
        for entry in self.dblinks:
            s.append(entry[0] + ": " + " ".join(entry[1]))
        return _write_kegg("DBLINKS", [_wrap_kegg(l, wrap_rule=id_wrap(9)) for l in s])

    def _pathway(self):
        s = []
        for entry in self.pathway:
            s.append(entry[0] + ' ' + " ".join(entry[1]))
        return _write_kegg("PATHWAY", [_wrap_kegg(l, wrap_rule=id_wrap(9)) for l in s])


def parse(handle):
    """Parse a KEGG Gene file, returning Record objects.

    This is an iterator function, typically used in a for loop.  For
    example, using one of the example KEGG files in the Biopython
    test suite,

    >>> with open("KEGG/gene.sample") as handle:
    ...     for record in parse(handle):
    ...         print("%s %s" % (record.entry, record.name[0]))
    ...
    b1174 minE
    b1175 minD


    """
    global keyword
    record = Record()
    for line in handle:
        if line[:3] == "///":
            yield record
            record = Record()
            continue
        if line[:12] != "            ":
            keyword = line[:12]
        data = line[12:].strip()
        if keyword == "ENTRY       ":
            words = data.split()
            record.entry = words[0]
        elif keyword == "NAME        ":
            data = data.strip(";")
            record.name.append(data)
        elif keyword == "DEFINITION  ":
            record.definition = data
        elif keyword == "ORTHOLOGY   ":
            id = data.split("  ")[0]
            name = data.split("  ")[-1]
            orthology = (id, name)
            record.orthology.append(orthology)
        elif keyword == "ORGANISM    ":
            id, name = data.split("  ")
            organism = (id, name)
            record.organism = organism
        elif keyword == "POSITION    ":
            record.position = data
        elif keyword == "MOTIF       ":
            key, values = data.split(": ")
            values = values.split()
            row = (key, values)
            record.motif.append(row)
        elif keyword == "DBLINKS     ":
            if ":" in data:
                key, values = data.split(": ")
                values = values.split()
                row = (key, values)
                record.dblinks.append(row)
            else:
                row = record.dblinks[-1]
                key, values = row
                values.extend(data.split())
                row = key, values
                record.dblinks[-1] = row
        elif keyword == "PATHWAY     ":
            if "  " in data:
                key, values = data.split("  ")
                row = (key, values)
                record.pathway.append(row)
            else:
                # row = record.pathway[-1]
                # key, values = row
                # values.extend(data.split())
                # row = key, values
                # record.pathway[-1] = row
                pass