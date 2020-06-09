from rdflib import Graph, Literal, URIRef
from rdflib import RDF, RDFS, FOAF, XSD, OWL
from pprint import pprint
import json
import re

g = Graph()

g.parse('wine.owl', format='turtle')

prefix = dict(g.namespaces())['']

RED_WINES = """
        SELECT *
        WHERE {{
            ?wine rdf:type :Color;
                :using_dark_grapes :Red;
        }}
        """
SWEET_WHITE_WINES = """
        SELECT *
        WHERE {{
            ?wine rdf:type :Color;
                :using_light_grapes :White;
                :have_0_sugar_and_7_12_alcohol :Dry;
        }}
        """
VINTAGE_WINES = """
        SELECT *
        WHERE {{
            ?wine rdf:type :Holding_period;
                :holding_not_less_than_2_years :Vintage;
        }}
        """



def save_output_file():
    with open('wine_output.owl', 'wb+') as f:
        f.write(g.serialize(format='turtle'))


def label(s):
    return str(g.label(s))


def normalize(name):
    return re.sub('\W', '_', name)


def ref(name):
    return URIRef(prefix + normalize(name))


def propvalue(key, prop):
    for o, p, s in g:
        if o == key and p == prop:
            return s


def add(entries):
    for e in entries:
        g.add(e)


def build_mapping():
    return dict((o, (propvalue(o, RDFS.domain), propvalue(o, RDFS.range)))
                for o, p, s in g
                if p == RDF.type and s == OWL.ObjectProperty)


mapping = build_mapping()
# {'manages': (Manager, Band)}

with open('new_data.json', 'r') as f:
    json_array = json.load(f)
    # print(json_array)
    for row in json_array:
        obj = row['Object']
        predicate = row['predicate']
        subject = row['subject']
        pred = ref(predicate)
        if pred not in mapping:
            raise Exception('Unknown predicate: ' + predicate)
        oc, sc = mapping[pred]
        add([
            (ref(obj), RDF.type, OWL.NamedIndividual),
            (ref(obj), RDF.type, oc),
            (ref(obj), RDFS.label, Literal(obj)),

            (ref(subject), RDF.type, OWL.NamedIndividual),
            (ref(subject), RDF.type, sc),
            (ref(subject), RDFS.label, Literal(subject)),

            (ref(obj), pred, ref(subject))
        ])


def execute(query):
    res = g.query(f"PREFIX : <{prefix}> " + query)
    if len(res.vars) == 1:
        return list(map(lambda x: x[res.vars[0]], res))
    else:
        return list(res)


all_red_wines = execute(RED_WINES)
print('Red wine is a', all_red_wines, '\n')

all_sweet_white_wines = execute(SWEET_WHITE_WINES)
print('Sweet White wine is a', all_sweet_white_wines, '\n')

all_vintage_wines = execute(VINTAGE_WINES)
print('Vintage wine is a', all_vintage_wines, '\n')



save_output_file()
