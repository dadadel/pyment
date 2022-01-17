#!/usr/bin/python
# -*- coding: utf-8 -*-
import pyment.docstring as docs

myelem = '    def my_method(self, first, second=None, third="value"):'
mydocs = '''        """This is a description of a method.
        It is on several lines.
        Several styles exists:
            -javadoc,
            -reST,
            -cstyle.
        It uses the javadoc style.

        @param first: the 1st argument.
        with multiple lines
        @type first: str
        @param second: the 2nd argument.
        @return: the result value
        @rtype: int
        @raise KeyError: raises a key error exception
        @raise OtherError: raises an other error exception

        """'''

mygrpdocs = '''
    """
    My desc of groups style.
    On two lines.

    Parameters:
      first: the 1st param
      second: the 2nd param
      third: the 3rd param

    Returns:
      a value in a string

    Raises:
      KeyError: when a key error
      OtherError: when an other error
    """'''

googledocs = '''"""This is a Google style docs.

    Args:
      first(str): this is the first param
      second: this is a second param
      third(str, optional): this is a third param

    Returns:
      This is a description of what is returned

    Raises:
      KeyError: raises an exception
      OtherError: when an other error
"""'''

mygrpdocs2 = '''
    """
    My desc of an other kind 
    of groups style.

    Params:
      first -- the 1st param
      second -- the 2nd param
      third -- the 3rd param

    Returns:
      a value in a string

    Raises:
      KeyError -- when a key error
      OtherError -- when an other error
    """'''

mynumpydocs = '''
    """
    My numpydoc description of a kind 
    of very exhautive numpydoc format docstring.

    Parameters
    ----------
    first : array_like
        the 1st param name `first`
    second :
        the 2nd param
    third : {'value', 'other'}, optional
        the 3rd param, by default 'value'

    Returns
    -------
    string
        a value in a string

    Raises
    ------
    KeyError
        when a key error
    OtherError
        when an other error

    See Also
    --------
    a_func : linked (optional), with things to say
             on several lines
    some blabla

    Note
    ----
    Some informations.

    Some maths also:
    .. math:: f(x) = e^{- x}

    References
    ----------
    Biblio with cited ref [1]_. The ref can be cited in Note section.

    .. [1] Adel Daouzli, Sylvain Saïghi, Michelle Rudolph, Alain Destexhe, 
       Sylvie Renaud: Convergence in an Adaptive Neural Network: 
       The Influence of Noise Inputs Correlation. IWANN (1) 2009: 140-148

    Examples
    --------
    This is example of use
    >>> print "a"
    a

    """'''


def torest(docs):
    docs = docs.replace("@", ":")
    docs = docs.replace(":return", ":returns")
    docs = docs.replace(":raise", ":raises")
    return docs


def testChekListParamsGoogledoc():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc)
    d._extract_docs_params()
    assert d.get_input_style() == "google"


def testAutoInputStyleGoogledoc():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc)
    assert d.get_input_style() == "google"


def testAutoInputStyleNumpydoc():
    doc = mynumpydocs
    d = docs.DocString(myelem, "    ", doc)
    assert d.get_input_style() == "numpydoc"


def testAutoInputStyleJavadoc():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    assert d.get_input_style() == "javadoc"


def testAutoInputStyleReST():
    doc = torest(mydocs)
    d = docs.DocString(myelem, "    ", doc)
    assert d.get_input_style() == "reST"


def testAutoInputStyleGroups():
    doc = mygrpdocs
    d = docs.DocString(myelem, "    ", doc)
    assert d.get_input_style() == "groups"


def testSameOutputJavadocReST():
    doc = mydocs
    dj = docs.DocString(myelem, "    ")
    dj.parse_docs(doc)
    doc = torest(mydocs)
    dr = docs.DocString(myelem, "    ")
    dr.parse_docs(doc)
    assert dj.get_raw_docs() == dr.get_raw_docs()


def testParsingElement():
    d = docs.DocString(myelem, "    ")
    assert d.element["deftype"] == "def"
    assert d.element["name"] == "my_method"
    assert len(d.element["params"]) == 3
    assert type(d.element["params"][0]["param"]) is str
    assert (d.element["params"][2]["param"], d.element["params"][2]["default"]) == (
        "third",
        '"value"',
    )


def testIfParsedDocs():
    doc = mydocs
    # nothing to parse
    d = docs.DocString(myelem, "    ")
    d.parse_docs()
    assert not d.parsed_docs
    # parse docstring given at init
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.parsed_docs
    # parse docstring given in parsing method
    d = docs.DocString(myelem, "    ")
    d.parse_docs(doc)
    assert d.parsed_docs


def testParsingDocsDesc():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["desc"].strip().startswith("This ")
    assert d.docs["in"]["desc"].strip().endswith("style.")


def testParsingGroupsDocsDesc():
    doc = mygrpdocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["desc"].strip().startswith("My ")
    assert d.docs["in"]["desc"].strip().endswith("lines.")


def testParsingNumpyDocsDesc():
    doc = mynumpydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["desc"].strip().startswith("My numpydoc")
    assert d.docs["in"]["desc"].strip().endswith("format docstring.")


def testParsingGoogleDocsDesc():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["desc"].strip().startswith("This is a Google style docs.")


def testParsingDocsParams():
    doc = torest(mydocs)
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["params"]) == 2
    assert type(d.docs["in"]["params"][1]) is tuple
    # param's name
    assert d.docs["in"]["params"][1][0] == "second"
    # param's type
    assert d.docs["in"]["params"][0][2] == "str"
    assert not d.docs["in"]["params"][1][2]
    # param's description
    assert d.docs["in"]["params"][0][1].startswith("the 1")


def testParsingGoogleDocsParams():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["params"]) == 3
    assert d.docs["in"]["params"][0][0] == "first"
    assert d.docs["in"]["params"][0][2] == "str"
    assert d.docs["in"]["params"][0][1].startswith("this is the first")
    assert not d.docs["in"]["params"][1][2]
    assert d.docs["in"]["params"][2][1].startswith("this is a third")
    assert d.docs["in"]["params"][2][2] == "str"


def testParsingGroupsDocsParams():
    doc = mygrpdocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["params"]) == 3
    assert d.docs["in"]["params"][0][0] == "first"
    assert d.docs["in"]["params"][0][1].startswith("the 1")
    assert d.docs["in"]["params"][2][1].startswith("the 3rd")


def testParsingGroups2DocsParams():
    doc = mygrpdocs2
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["params"]) == 3
    assert d.docs["in"]["params"][0][0] == "first"
    assert d.docs["in"]["params"][0][1].startswith("the 1")
    assert d.docs["in"]["params"][2][1].startswith("the 3rd")


def testParsingNumpyDocsParams():
    doc = mynumpydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["params"]) == 3
    assert d.docs["in"]["params"][0][0] == "first"
    assert d.docs["in"]["params"][0][2] == "array_like"
    assert d.docs["in"]["params"][0][1].strip().startswith("the 1")
    assert not d.docs["in"]["params"][1][2]
    assert d.docs["in"]["params"][2][1].strip().endswith("default 'value'")


def testParsingDocsRaises():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    d.generate_docs()
    assert len(d.docs["in"]["raises"]) == 2
    assert d.docs["in"]["raises"][0][0].startswith("KeyError")
    assert d.docs["in"]["raises"][0][1].startswith("raises a key")
    assert d.docs["in"]["raises"][1][0].startswith("OtherError")
    assert d.docs["in"]["raises"][1][1].startswith("raises an other")


def testParsingGoogleDocsRaises():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["raises"]) == 2
    assert d.docs["in"]["raises"][0][0] == "KeyError"
    assert d.docs["in"]["raises"][0][1].startswith("raises an")
    assert d.docs["in"]["raises"][1][0] == "OtherError"
    assert d.docs["in"]["raises"][1][1].startswith("when an other")


def testParsingGroupsDocsRaises():
    doc = mygrpdocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["raises"]) == 2
    assert d.docs["in"]["raises"][0][0] == "KeyError"
    assert d.docs["in"]["raises"][0][1].startswith("when a key")
    assert d.docs["in"]["raises"][1][0] == "OtherError"
    assert d.docs["in"]["raises"][1][1].startswith("when an other")


def testParsingGroups2DocsRaises():
    doc = mygrpdocs2
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["raises"]) == 2
    assert d.docs["in"]["raises"][0][0] == "KeyError"
    assert d.docs["in"]["raises"][0][1].startswith("when a key")
    assert d.docs["in"]["raises"][1][0] == "OtherError"
    assert d.docs["in"]["raises"][1][1].startswith("when an other")


def testParsingNumpyDocsRaises():
    doc = mynumpydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert len(d.docs["in"]["raises"]) == 2
    assert d.docs["in"]["raises"][0][0] == "KeyError"
    assert d.docs["in"]["raises"][0][1].strip().startswith("when a key")
    assert d.docs["in"]["raises"][1][0] == "OtherError"
    assert d.docs["in"]["raises"][1][1].strip().startswith("when an other")


def testParsingDocsReturn():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["return"].startswith("the result")
    assert d.docs["in"]["rtype"] == "int"


def testParsingGroupsDocsReturn():
    doc = mygrpdocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["return"] == "a value in a string"


def testParsingGoogleDocsReturn():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["return"][0][1] == "This is a description of what is returned"


def testParsingNumpyDocsReturn():
    doc = mynumpydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    assert d.docs["in"]["return"][0][1] == "a value in a string"
    d.set_output_style("numpydoc")


def testGeneratingDocsDesc():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    d.generate_docs()
    assert d.docs["out"]["desc"] == d.docs["in"]["desc"]


def testGeneratingDocsReturn():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    d.generate_docs()
    assert d.docs["out"]["return"].startswith("the result")
    assert d.docs["out"]["rtype"] == "int"


def testGeneratingDocsRaise():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    d.generate_docs()
    assert len(d.docs["out"]["raises"]) == 2
    assert d.docs["out"]["raises"][0][0].startswith("KeyError")
    assert d.docs["out"]["raises"][0][1].startswith("raises a key")
    assert d.docs["out"]["raises"][1][0].startswith("OtherError")
    assert d.docs["out"]["raises"][1][1].startswith("raises an other")


def testGeneratingDocsParams():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc)
    d.parse_docs()
    d.generate_docs()
    assert len(d.docs["out"]["params"]) == 3
    assert type(d.docs["out"]["params"][2]) is tuple
    assert d.docs["out"]["params"][2] == ("third", "", None, '"value"')
    # param's description
    assert d.docs["out"]["params"][1][1].startswith("the 2")


def testGeneratingDocsParamsTypeStubs():
    doc = mydocs
    d = docs.DocString(myelem, "    ", doc, type_stub=True)
    d.parse_docs()
    d.generate_docs()
    assert ":type second: " in d.docs["out"]["raw"]
    assert ":type third: " in d.docs["out"]["raw"]


def testGeneratingGoogleDocsParamsTypeStubs():
    doc = googledocs
    d = docs.DocString(myelem, "    ", doc, type_stub=True)
    d.parse_docs()
    d.generate_docs()
    assert ":type second: " in d.docs["out"]["raw"]


def testGeneratingGroupsDocsParamsTypeStubs():
    doc = mygrpdocs
    d = docs.DocString(myelem, "    ", doc, type_stub=True)
    d.parse_docs()
    d.generate_docs()
    assert ":type first: " in d.docs["out"]["raw"]
    assert ":type second: " in d.docs["out"]["raw"]
    assert ":type third: " in d.docs["out"]["raw"]


def testGeneratingGroups2DocsParamsTypeStubs():
    doc = mygrpdocs2
    d = docs.DocString(myelem, "    ", doc, type_stub=True)
    d.parse_docs()
    d.generate_docs()
    assert ":type first: " in d.docs["out"]["raw"]
    assert ":type second: " in d.docs["out"]["raw"]
    assert ":type third: " in d.docs["out"]["raw"]


def testGeneratingNumpyDocsParamsTypeStubs():
    doc = mynumpydocs
    d = docs.DocString(myelem, "    ", doc, type_stub=True)
    d.parse_docs()
    d.generate_docs()
    assert ":type second: " in d.docs["out"]["raw"]


def testNoParam():
    elem = "    def noparam():"
    doc = """        '''the no param docstring
    '''"""
    d = docs.DocString(elem, "    ", doc, input_style="javadoc")
    d.parse_docs()
    d.generate_docs()
    assert not d.docs["out"]["params"]


def testOneLineDocs():
    elem = "    def oneline():"
    doc = """        '''the one line docstring
    '''"""
    d = docs.DocString(elem, "    ", doc, input_style="javadoc")
    d.parse_docs()
    d.generate_docs()
    assert not d.docs["out"]["raw"].count("\n")
