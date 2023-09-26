#!/usr/bin/python
"""Tests for docstring module."""


import pyment.docstring as docs


def torest(docstring: str) -> str:
    """Turn docstring to rest format.

    Parameters
    ----------
    docstring : str
        String to transform

    Returns
    -------
    str
        Transformed string
    """
    docstring = docstring.replace("@", ":")
    docstring = docstring.replace(":return", ":returns")
    return docstring.replace(":raise", ":raises")


class TestDocStrings:
    """Semi-integration tests for docstring module."""

    def setup_class(self) -> None:
        """Set up class by defining loading dictionary of test demo files."""
        self.myelem = '    def my_method(self, first, second=None, third="value"):'
        self.mydocs = '''        """This is a description of a method.
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

        self.mygrpdocs = '''
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

        self.googledocs = '''"""This is a Google style docs.

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

        self.mygrpdocs2 = '''
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

        self.mynumpydocs = '''
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

    def test_check_list_params_googledoc(self) -> None:
        """Check that input style is correctly parsed in google style."""
        doc = self.googledocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring._extract_docs_params()
        assert docstring.get_input_style() == "google"

    def test_auto_input_style_googledoc(self) -> None:
        """Check that input style is correctly parsed in google style."""
        doc = self.googledocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        assert docstring.get_input_style() == "google"

    def test_auto_input_style_numpydoc(self) -> None:
        """Check that input style is correctly parsed in numpy style."""
        doc = self.mynumpydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        assert docstring.get_input_style() == "numpydoc"

    def test_auto_input_style_javadoc(self) -> None:
        """Check that input style is correctly parsed in java style."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        assert docstring.get_input_style() == "javadoc"

    def test_auto_input_style_reST(self) -> None:  # noqa: N802
        """Check that input style is correctly parsed in rest style."""
        doc = torest(self.mydocs)
        docstring = docs.DocString(self.myelem, "    ", doc)
        assert docstring.get_input_style() == "reST"

    def test_auto_input_style_groups(self) -> None:
        """Check that input style is correctly parsed in groups style."""
        doc = self.mygrpdocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        assert docstring.get_input_style() == "groups"

    def test_same_output_javadoc_reST(self) -> None:  # noqa: N802
        """Check that java and rest styles produce compatible output."""
        doc = self.mydocs
        dj = docs.DocString(self.myelem, "    ")
        dj.parse_docs(doc)
        doc = torest(self.mydocs)
        dr = docs.DocString(self.myelem, "    ")
        dr.parse_docs(doc)
        assert dj.get_raw_docs() == dr.get_raw_docs()

    def test_parsing_element(self) -> None:
        """Check that elements are parsed correctly."""
        docstring = docs.DocString(self.myelem, "    ")
        assert docstring.element["deftype"] == "def"
        assert docstring.element["name"] == "my_method"
        assert len(docstring.element["params"]) == 3
        assert isinstance(docstring.element["params"][0]["param"], str)
        assert (
            docstring.element["params"][2]["param"],
            docstring.element["params"][2]["default"],
        ) == (
            "third",
            '"value"',
        )

    def test_if_parsed_docs(self) -> None:
        """Check that parsing works correctly."""
        doc = self.mydocs
        # nothing to parse
        docstring = docs.DocString(self.myelem, "    ")
        docstring.parse_docs()
        assert not docstring.parsed_docs
        # parse docstring given at init
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.parsed_docs
        # parse docstring given in parsing method
        docstring = docs.DocString(self.myelem, "    ")
        docstring.parse_docs(doc)
        assert docstring.parsed_docs

    def test_parsing_docs_desc(self) -> None:
        """Check that description is parsed correctly."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.docs["in"]["desc"].strip().startswith("This ")
        assert docstring.docs["in"]["desc"].strip().endswith("style.")

    def test_parsing_groups_docs_desc(self) -> None:
        """Check that description is parsed correctly in group style."""
        doc = self.mygrpdocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.docs["in"]["desc"].strip().startswith("My ")
        assert docstring.docs["in"]["desc"].strip().endswith("lines.")

    def test_parsing_numpy_docs_desc(self) -> None:
        """Check that description is parsed correctly in numpy style."""
        doc = self.mynumpydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.docs["in"]["desc"].strip().startswith("My numpydoc")
        assert docstring.docs["in"]["desc"].strip().endswith("format docstring.")

    def test_parsing_google_docs_desc(self) -> None:
        """Check that description is parsed correctly in google style."""
        doc = self.googledocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert (
            docstring.docs["in"]["desc"]
            .strip()
            .startswith("This is a Google style docs.")
        )

    def test_parsing_docs_params(self) -> None:
        """Check that parameters are parsed correctly in rest style."""
        doc = torest(self.mydocs)
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["params"]) == 2
        assert type(docstring.docs["in"]["params"][1]) is tuple
        # param's name
        assert docstring.docs["in"]["params"][1][0] == "second"
        # param's type
        assert docstring.docs["in"]["params"][0][2] == "str"
        assert not docstring.docs["in"]["params"][1][2]
        # param's description
        assert docstring.docs["in"]["params"][0][1].startswith("the 1")

    def test_parsing_google_docs_params(self) -> None:
        """Check that parameters are parsed correctly in google style."""
        doc = self.googledocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["params"]) == 3
        assert docstring.docs["in"]["params"][0][0] == "first"
        assert docstring.docs["in"]["params"][0][2] == "str"
        assert docstring.docs["in"]["params"][0][1].startswith("this is the first")
        assert not docstring.docs["in"]["params"][1][2]
        assert docstring.docs["in"]["params"][2][1].startswith("this is a third")
        assert docstring.docs["in"]["params"][2][2] == "str"

    def test_parsing_groups_docs_params(self) -> None:
        """Check that parameters are parsed correctly in group style."""
        doc = self.mygrpdocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["params"]) == 3
        assert docstring.docs["in"]["params"][0][0] == "first"
        assert docstring.docs["in"]["params"][0][1].startswith("the 1")
        assert docstring.docs["in"]["params"][2][1].startswith("the 3rd")

    def test_parsing_groups2_docs_params(self) -> None:
        """Check that parameters are parsed correctly in group style."""
        doc = self.mygrpdocs2
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["params"]) == 3
        assert docstring.docs["in"]["params"][0][0] == "first"
        assert docstring.docs["in"]["params"][0][1].startswith("the 1")
        assert docstring.docs["in"]["params"][2][1].startswith("the 3rd")

    def test_parsing_numpy_docs_params(self) -> None:
        """Check that parameters are parsed correctly in numpy style."""
        doc = self.mynumpydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["params"]) == 3
        assert docstring.docs["in"]["params"][0][0] == "first"
        assert docstring.docs["in"]["params"][0][2] == "array_like"
        assert docstring.docs["in"]["params"][0][1].strip().startswith("the 1")
        assert not docstring.docs["in"]["params"][1][2]
        assert docstring.docs["in"]["params"][2][1].strip().endswith("default 'value'")

    def test_parsing_docs_raises(self) -> None:
        """Check that raises section is parsed correctly in rest style."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        docstring.generate_docs()
        assert len(docstring.docs["in"]["raises"]) == 2
        assert docstring.docs["in"]["raises"][0][0].startswith("KeyError")
        assert docstring.docs["in"]["raises"][0][1].startswith("raises a key")
        assert docstring.docs["in"]["raises"][1][0].startswith("OtherError")
        assert docstring.docs["in"]["raises"][1][1].startswith("raises an other")

    def test_parsing_google_docs_raises(self) -> None:
        """Check that raises section is parsed correctly in google style."""
        doc = self.googledocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["raises"]) == 2
        assert docstring.docs["in"]["raises"][0][0] == "KeyError"
        assert docstring.docs["in"]["raises"][0][1].startswith("raises an")
        assert docstring.docs["in"]["raises"][1][0] == "OtherError"
        assert docstring.docs["in"]["raises"][1][1].startswith("when an other")

    def test_parsing_groups_docs_raises(self) -> None:
        """Check that raises section is parsed correctly in group style."""
        doc = self.mygrpdocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["raises"]) == 2
        assert docstring.docs["in"]["raises"][0][0] == "KeyError"
        assert docstring.docs["in"]["raises"][0][1].startswith("when a key")
        assert docstring.docs["in"]["raises"][1][0] == "OtherError"
        assert docstring.docs["in"]["raises"][1][1].startswith("when an other")

    def test_parsing_groups2_docs_raises(self) -> None:
        """Check that raises section is parsed correctly in group style."""
        doc = self.mygrpdocs2
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["raises"]) == 2
        assert docstring.docs["in"]["raises"][0][0] == "KeyError"
        assert docstring.docs["in"]["raises"][0][1].startswith("when a key")
        assert docstring.docs["in"]["raises"][1][0] == "OtherError"
        assert docstring.docs["in"]["raises"][1][1].startswith("when an other")

    def test_parsing_numpy_docs_raises(self) -> None:
        """Check that raises section is parsed correctly in numpy style."""
        doc = self.mynumpydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert len(docstring.docs["in"]["raises"]) == 2
        assert docstring.docs["in"]["raises"][0][0] == "KeyError"
        assert docstring.docs["in"]["raises"][0][1].strip().startswith("when a key")
        assert docstring.docs["in"]["raises"][1][0] == "OtherError"
        assert docstring.docs["in"]["raises"][1][1].strip().startswith("when an other")

    def test_parsing_docs_return(self) -> None:
        """Check that return section is parsed correctly in rest style."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.docs["in"]["return"].startswith("the result")
        assert docstring.docs["in"]["rtype"] == "int"

    def test_parsing_groups_docs_return(self) -> None:
        """Check that return section is parsed correctly in group style."""
        doc = self.mygrpdocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.docs["in"]["return"] == "a value in a string"

    def test_parsing_google_docs_return(self) -> None:
        """Check that return section is parsed correctly in google style."""
        doc = self.googledocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert (
            docstring.docs["in"]["return"][0][1]
            == "This is a description of what is returned"
        )

    def test_parsing_numpy_docs_return(self) -> None:
        """Check that return section is parsed correctly in numpy style."""
        doc = self.mynumpydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        assert docstring.docs["in"]["return"][0][1] == "a value in a string"
        docstring.set_output_style("numpydoc")

    def test_generating_docs_desc(self) -> None:
        """Check that description output is correctly generated."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        docstring.generate_docs()
        assert docstring.docs["out"]["desc"] == docstring.docs["in"]["desc"]

    def test_generating_docs_return(self) -> None:
        """Check that return output is correctly generated."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        docstring.generate_docs()
        assert docstring.docs["out"]["return"].startswith("the result")
        assert docstring.docs["out"]["rtype"] == "int"

    def test_generating_docs_raise(self) -> None:
        """Check that raises output is correctly generated."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        docstring.generate_docs()
        assert len(docstring.docs["out"]["raises"]) == 2
        assert docstring.docs["out"]["raises"][0][0].startswith("KeyError")
        assert docstring.docs["out"]["raises"][0][1].startswith("raises a key")
        assert docstring.docs["out"]["raises"][1][0].startswith("OtherError")
        assert docstring.docs["out"]["raises"][1][1].startswith("raises an other")

    def test_generating_docs_params(self) -> None:
        """Check that params output is correctly generated."""
        doc = self.mydocs
        docstring = docs.DocString(self.myelem, "    ", doc)
        docstring.parse_docs()
        docstring.generate_docs()
        assert len(docstring.docs["out"]["params"]) == 3
        assert isinstance(docstring.docs["out"]["params"][2],tuple)
        assert docstring.docs["out"]["params"][2] == ("third", "", None, '"value"')
        # param's description
        assert docstring.docs["out"]["params"][1][1].startswith("the 2")

    def test_generating_docs_params_type_stubs(self) -> None:
        """Check that params are correctly generated from type stubs in rest."""
        doc = self.mydocs
        docstring = docs.DocString(
            self.myelem, "    ", doc, type_stub=True, output_style="reST"
        )
        docstring.parse_docs()
        docstring.generate_docs()
        assert ":type second: " in docstring.docs["out"]["raw"]
        assert ":type third: " in docstring.docs["out"]["raw"]

    def test_generating_google_docs_params_type_stubs(self) -> None:
        """Check that params are correctly generated from type stubs in google style."""
        doc = self.googledocs
        docstring = docs.DocString(
            self.myelem, "    ", doc, type_stub=True, output_style="reST"
        )
        docstring.parse_docs()
        docstring.generate_docs()
        assert ":type second: " in docstring.docs["out"]["raw"]

    def test_generating_groups_docs_params_type_stubs(self) -> None:
        """Check that params are correctly generated from type stubs in group style."""
        doc = self.mygrpdocs
        docstring = docs.DocString(
            self.myelem, "    ", doc, type_stub=True, output_style="reST"
        )
        docstring.parse_docs()
        docstring.generate_docs()
        assert ":type first: " in docstring.docs["out"]["raw"]
        assert ":type second: " in docstring.docs["out"]["raw"]
        assert ":type third: " in docstring.docs["out"]["raw"]

    def test_generating_groups2_docs_params_type_stubs(self) -> None:
        """Check that params are correctly generated from type stubs in group style."""
        doc = self.mygrpdocs2
        docstring = docs.DocString(
            self.myelem, "    ", doc, type_stub=True, output_style="reST"
        )
        docstring.parse_docs()
        docstring.generate_docs()
        assert ":type first: " in docstring.docs["out"]["raw"]
        assert ":type second: " in docstring.docs["out"]["raw"]
        assert ":type third: " in docstring.docs["out"]["raw"]

    def test_generating_numpy_docs_params_type_stubs(self) -> None:
        """Check that params are correctly generated from type stubs in numpy style."""
        doc = self.mynumpydocs
        docstring = docs.DocString(
            self.myelem, "    ", doc, type_stub=True, output_style="reST"
        )
        docstring.parse_docs()
        docstring.generate_docs()
        assert ":type second: " in docstring.docs["out"]["raw"]

    def test_no_param(self) -> None:
        """Check that params section is correctly generated in no param case."""
        elem = "    def noparam():"
        doc = """        '''the no param docstring
        '''"""
        docstring = docs.DocString(elem, "    ", doc, input_style="javadoc")
        docstring.parse_docs()
        docstring.generate_docs()
        assert not docstring.docs["out"]["params"]

    def test_one_line_docs(self) -> None:
        """Check that online doc strings remain one line."""
        elem = "    def oneline(self):"
        doc = """        '''the one line docstring
        '''"""
        docstring = docs.DocString(
            elem, "    ", doc, input_style="javadoc", first_line=True
        )
        docstring.parse_docs()
        docstring.generate_docs()
        assert docstring.docs["out"]["raw"].count("\n") == 0
