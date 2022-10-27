#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/10/08 13:20
# @Author  : 
from Bio.KEGG import _default_wrap, _wrap_kegg, _write_kegg
import sys

# Set up line wrapping rules (see Bio.KEGG._wrap_kegg)
name_wrap = [0, "", (" ", "$", 1, 1), ("-", "$", 1, 1)]
id_wrap = _default_wrap

class KeggKoRecord:
    """Holds info from a KEGG Map record.

    Attributes:
     - entry       The entry identifier.
     - name         map names.
     - class        The definition for the gene.
     - pathway_map 
     - module      
     - dblinks     
     - 

    """

    def __init__(self):
        """Initialize new record."""
        self.entry = ""
        self.name = ""
        self.description = ""
        self.organism = ""
        self.dblinks = ""
        self._class = ""
        self.orthology = []


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

def parse_ko(handle):
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
    record = KeggKoRecord()
    start_k = False
    for line in handle:
        if line[:3] == "///":
            yield record
            record = KeggMapRecord()
            continue
        if line[:12] != "            ":
            keyword = line[:12]
            data = line[12:].strip()
        else:
            data = line[12:].strip()
            if start_k and data[0] == "K" and data[6] == "":
                record.orthology.append(ko.split(" ")[0].strip()) 
        if keyword == "ENTRY       ":
            words = data.split()
            record.entry = words[0]
        elif keyword == "NAME        ":
            data = data.strip(";")
            record.name = data
        elif keyword == "DESCRIPTION ":
            record.definition = data
        elif keyword == "ORGANISM    ":
            organism = data.strip()
            record.organism = organism
        elif keyword == "ORTHOLOGY   ":
            ko = data.strip()
            start_k = True
            record.orthology.append(ko.split(" ")[0].strip())
        elif keyword == "DBLINKS     ":
            record.dblinks = data.strip()
        elif keyword == "CLASS       ":
            class11 = data.strip()
            record._class = class11


class KeggMapRecord:
    """Holds info from a KEGG Map record.

    Attributes:
     - entry       The entry identifier.
     - name         map names.
     - class        The definition for the gene.
     - pathway_map 
     - module      
     - dblinks     
     - 

    """

    def __init__(self):
        """Initialize new record."""
        self.entry = ""
        self.name = ""
        self.description = ""
        self.organism = ""
        self.dblinks = ""
        self._class = ""


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
    record = KeggMapRecord()
    for line in handle:
        if line[:3] == "///":
            yield record
            record = KeggMapRecord()
            continue
        if line[:12] != "            ":
            keyword = line[:12]
            data = line[12:].strip()
        if keyword == "ENTRY       ":
            words = data.split()
            record.entry = words[0]
        elif keyword == "NAME        ":
            data = data.strip(";")
            record.name = data
        elif keyword == "DESCRIPTION ":
            record.description = data
        elif keyword == "ORGANISM    ":
            organism = data.strip()
            record.organism = organism
        elif keyword == "DBLINKS     ":
            record.dblinks = data.strip()
        elif keyword == "CLASS       ":
            class11 = data.strip()
            record._class = class11

if __name__ == "__main__":
    map_file = sys.argv[1]
    with open(map_file, "r") as mf:
        # for map_rec in parse_ko(mf):
        #     print(map_rec.entry)
        #     print(map_rec.orthology)
        for map_rec in parse(mf):
            print("\t".join([map_rec.entry, map_rec.name, map_rec._class, map_rec.description, map_rec.dblinks, map_rec.organism]))
