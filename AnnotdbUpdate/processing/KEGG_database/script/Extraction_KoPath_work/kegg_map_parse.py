#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/10/08 13:20
# @Author  : 
from Bio.KEGG import _default_wrap, _wrap_kegg, _write_kegg
import sys
import json

# Set up line wrapping rules (see Bio.KEGG._wrap_kegg)
name_wrap = [0, "", (" ", "$", 1, 1), ("-", "$", 1, 1)]
id_wrap = _default_wrap

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
        self.pathway = []
        self.dblinks = []
        self.genes = []
        self.module = []
        self.orthology = []
        self.compund = []


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

def parse_map(handle):
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
    start_k = False
    ele = ""
    for line in handle:
        if line[:3] == "///":
            yield record
            record = KeggMapRecord()
            continue
        if line[:12] != "            ":
            keyword = line[:12]
            data = line[12:].strip()

            # print keyword
            if keyword == "BRITE       ":
                ele = "brite"
            elif keyword == "ENTRY       ":
                ele == "entry"
                words = data.split()
                record.entry = words[0]
            elif keyword == "NAME        ":
                data = data.strip(";")
                record.name = data
                ele = "name"
            elif keyword == "DESCRIPTION ":
                record.description = data
                ele = "definition"
            elif keyword == "ORGANISM    ":
                organism = data.strip()
                record.organism = organism
                ele = organism
            elif keyword == "ORTHOLOGY   ":
                ko = data.strip()
                start_k = True
                record.orthology.append(ko.split(" ")[0].strip())
                ele = "orthology"
            elif keyword == "DBLINKS     ":
                record.dblinks = data.strip()
                ele = "dblinks"
            elif keyword == "PATHWAY     ":
                ele = "pathway"
                path = [data.split("  ")[0], data.split("  ")[1]]
                record.pathway.append(path)
            elif keyword == "MODULE      ":
                ele = "module"
                module = data.strip()
                record.module.append(module.split(" ")[0].strip())
            elif keyword == "COMPOUND    ":
                ele = "compund"
                compund = data.strip()
                record.compund.append(compund.split(" ")[0].strip())
            else:
                ele = keyword
        else:
            data = line[12:].strip()
            # print ele
            if ele == "orthology":
                # print data
                ko = data.strip()
                start_k = True
                record.orthology.append(ko.split(" ")[0].strip())
            if ele == "module":
                module = data.strip()
                record.module.append(module.split(" ")[0].strip())
            if ele == "compund":
                compund = data.strip()
                record.module.append(compund.split(" ")[0].strip())


def convert_one_map(map_file, to_type="json"):
    ko_dict = dict()
    with open(map_file, "r") as kof:
        for ko_rec in parse_map(kof):
            ko_dict.update({ko_rec.entry: {
                "entry": ko_rec.entry,
                "name": ko_rec.name,
                "description": ko_rec.description,
                "module": ko_rec.pathway,
                "dblinks": ko_rec.dblinks,
                "compund": ko_rec.compund,
                "orthology": ko_rec.orthology
            }})

    with open(map_file + ".json", "w") as f:
        f.write(json.dumps(ko_dict, indent=4))
    return ko_dict



if __name__ == "__main__":
    import glob
    map_files = glob.glob("*")
    for map_file in map_files:
        map_dict = convert_one_map(map_file)

        with open(map_file + ".ko", "w") as map2ko:
            for m, d in map_dict.items():
                for k in d["orthology"]:
                    map2ko.write("path:{}\tko:{}\n".format(m, k))
