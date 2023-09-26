#!/usr/bin/python
# -*- coding: utf-8 -*-
import pyment.docstring as docs




def torest(docs):
    docs = docs.replace("@", ":")
    docs = docs.replace(":return", ":returns")
    docs = docs.replace(":raise", ":raises")
    return docs


class TestDocStrings:

    def setup_class(self):
        """Setup class by defining loading dictionary of test demo files."""
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

    def test_check_list_params_googledoc(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc)
        d._extract_docs_params()
        assert d.get_input_style() == 'google'

    def test_auto_input_style_googledoc(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc)
        assert d.get_input_style() == 'google'

    def test_auto_input_style_numpydoc(self):
        doc = self.mynumpydocs
        d = docs.DocString(self.myelem, '    ', doc)
        assert d.get_input_style() == 'numpydoc'

    def test_auto_input_style_javadoc(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        assert d.get_input_style() == 'javadoc'

    def test_auto_input_style_reST(self):
        doc = torest(self.mydocs)
        d = docs.DocString(self.myelem, '    ', doc)
        assert d.get_input_style() == 'reST'

    def test_auto_input_style_groups(self):
        doc = self.mygrpdocs
        d = docs.DocString(self.myelem, '    ', doc)
        assert d.get_input_style() == 'groups'

    def test_same_output_javadoc_reST(self):
        doc = self.mydocs
        dj = docs.DocString(self.myelem, '    ')
        dj.parse_docs(doc)
        doc = torest(self.mydocs)
        dr = docs.DocString(self.myelem, '    ')
        dr.parse_docs(doc)
        assert dj.get_raw_docs() == dr.get_raw_docs()

    def test_parsing_element(self):
        d = docs.DocString(self.myelem, '    ')
        assert d.element['deftype'] == 'def'
        assert d.element['name'] == 'my_method'
        assert len(d.element['params']) == 3
        assert type(d.element['params'][0]['param']) is str
        assert (d.element['params'][2]['param'], d.element['params'][2]['default']) == ('third', '"value"')

    def test_if_parsed_docs(self):
        doc = self.mydocs
        # nothing to parse
        d = docs.DocString(self.myelem, '    ')
        d.parse_docs()
        assert not d.parsed_docs
        # parse docstring given at init
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.parsed_docs
        # parse docstring given in parsing method
        d = docs.DocString(self.myelem, '    ')
        d.parse_docs(doc)
        assert d.parsed_docs

    def test_parsing_docs_desc(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['desc'].strip().startswith('This ')
        assert d.docs['in']['desc'].strip().endswith('style.')

    def test_parsing_groups_docs_desc(self):
        doc = self.mygrpdocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['desc'].strip().startswith('My ')
        assert d.docs['in']['desc'].strip().endswith('lines.')

    def test_parsing_numpy_docs_desc(self):
        doc = self.mynumpydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['desc'].strip().startswith('My numpydoc')
        assert d.docs['in']['desc'].strip().endswith('format docstring.')

    def test_parsing_google_docs_desc(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['desc'].strip().startswith('This is a Google style docs.')

    def test_parsing_docs_params(self):
        doc = torest(self.mydocs)
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['params']) == 2
        assert type(d.docs['in']['params'][1]) is tuple
        # param's name
        assert d.docs['in']['params'][1][0] == 'second'
        # param's type
        assert d.docs['in']['params'][0][2] == 'str'
        assert not d.docs['in']['params'][1][2]
        # param's description
        assert d.docs['in']['params'][0][1].startswith("the 1")

    def test_parsing_google_docs_params(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['params']) == 3
        assert d.docs['in']['params'][0][0] == 'first'
        assert d.docs['in']['params'][0][2] == 'str'
        assert d.docs['in']['params'][0][1].startswith('this is the first')
        assert not d.docs['in']['params'][1][2]
        assert d.docs['in']['params'][2][1].startswith('this is a third')
        assert d.docs['in']['params'][2][2] == 'str'

    def test_parsing_groups_docs_params(self):
        doc = self.mygrpdocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['params']) == 3
        assert d.docs['in']['params'][0][0] == 'first'
        assert d.docs['in']['params'][0][1].startswith('the 1')
        assert d.docs['in']['params'][2][1].startswith('the 3rd')

    def test_parsing_groups2_docs_params(self):
        doc = self.mygrpdocs2
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['params']) == 3
        assert d.docs['in']['params'][0][0] == 'first'
        assert d.docs['in']['params'][0][1].startswith('the 1')
        assert d.docs['in']['params'][2][1].startswith('the 3rd')

    def test_parsing_numpy_docs_params(self):
        doc = self.mynumpydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['params']) == 3
        assert d.docs['in']['params'][0][0] == 'first'
        assert d.docs['in']['params'][0][2] == 'array_like'
        assert d.docs['in']['params'][0][1].strip().startswith('the 1')
        assert not d.docs['in']['params'][1][2]
        assert d.docs['in']['params'][2][1].strip().endswith("default 'value'")

    def test_parsing_docs_raises(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        assert len(d.docs['in']['raises']) == 2
        assert d.docs['in']['raises'][0][0].startswith('KeyError')
        assert d.docs['in']['raises'][0][1].startswith('raises a key')
        assert d.docs['in']['raises'][1][0].startswith('OtherError')
        assert d.docs['in']['raises'][1][1].startswith('raises an other')

    def test_parsing_google_docs_raises(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['raises']) == 2
        assert d.docs['in']['raises'][0][0] == 'KeyError'
        assert d.docs['in']['raises'][0][1].startswith('raises an')
        assert d.docs['in']['raises'][1][0] == 'OtherError'
        assert d.docs['in']['raises'][1][1].startswith('when an other')

    def test_parsing_groups_docs_raises(self):
        doc = self.mygrpdocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['raises']) == 2
        assert d.docs['in']['raises'][0][0] == 'KeyError'
        assert d.docs['in']['raises'][0][1].startswith('when a key')
        assert d.docs['in']['raises'][1][0] == 'OtherError'
        assert d.docs['in']['raises'][1][1].startswith('when an other')

    def test_parsing_groups2_docs_raises(self):
        doc = self.mygrpdocs2
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['raises']) == 2
        assert d.docs['in']['raises'][0][0] == 'KeyError'
        assert d.docs['in']['raises'][0][1].startswith('when a key')
        assert d.docs['in']['raises'][1][0] == 'OtherError'
        assert d.docs['in']['raises'][1][1].startswith('when an other')

    def test_parsing_numpy_docs_raises(self):
        doc = self.mynumpydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert len(d.docs['in']['raises']) == 2
        assert d.docs['in']['raises'][0][0] == 'KeyError'
        assert d.docs['in']['raises'][0][1].strip().startswith('when a key')
        assert d.docs['in']['raises'][1][0] == 'OtherError'
        assert d.docs['in']['raises'][1][1].strip().startswith('when an other')

    def test_parsing_docs_return(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['return'].startswith('the result')
        assert d.docs['in']['rtype'] == 'int'

    def test_parsing_groups_docs_return(self):
        doc = self.mygrpdocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['return'] == 'a value in a string'

    def test_parsing_google_docs_return(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['return'][0][1] == 'This is a description of what is returned'

    def test_parsing_numpy_docs_return(self):
        doc = self.mynumpydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        assert d.docs['in']['return'][0][1] == 'a value in a string'
        d.set_output_style('numpydoc')

    def test_generating_docs_desc(self):
        doc =self. mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        assert d.docs['out']['desc'] == d.docs['in']['desc']

    def test_generating_docs_return(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        assert d.docs['out']['return'].startswith('the result')
        assert d.docs['out']['rtype'] == 'int'

    def test_generating_docs_raise(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        assert len(d.docs['out']['raises']) == 2
        assert d.docs['out']['raises'][0][0].startswith('KeyError')
        assert d.docs['out']['raises'][0][1].startswith('raises a key')
        assert d.docs['out']['raises'][1][0].startswith('OtherError')
        assert d.docs['out']['raises'][1][1].startswith('raises an other')

    def test_generating_docs_params(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        assert len(d.docs['out']['params']) == 3
        assert type(d.docs['out']['params'][2]) is tuple
        assert d.docs['out']['params'][2] == ('third', '', None, '"value"')
        # param's description
        assert d.docs['out']['params'][1][1].startswith("the 2")

    def test_generating_docs_params_type_stubs(self):
        doc = self.mydocs
        d = docs.DocString(self.myelem, '    ', doc, type_stub=True, output_style= "reST")
        d.parse_docs()
        d.generate_docs()
        assert ':type second: ' in d.docs['out']['raw']
        assert ':type third: ' in d.docs['out']['raw']

    def test_generating_google_docs_params_type_stubs(self):
        doc = self.googledocs
        d = docs.DocString(self.myelem, '    ', doc, type_stub=True, output_style= "reST")
        d.parse_docs()
        d.generate_docs()
        assert ':type second: ' in d.docs['out']['raw']

    def test_generating_groups_docs_params_type_stubs(self):
        doc = self.mygrpdocs
        d = docs.DocString(self.myelem, '    ', doc, type_stub=True, output_style= "reST")
        d.parse_docs()
        d.generate_docs()
        assert ':type first: ' in d.docs['out']['raw']
        assert ':type second: ' in d.docs['out']['raw']
        assert ':type third: ' in d.docs['out']['raw']

    def test_generating_groups2_docs_params_type_stubs(self):
        doc = self.mygrpdocs2
        d = docs.DocString(self.myelem, '    ', doc, type_stub=True, output_style= "reST")
        d.parse_docs()
        d.generate_docs()
        assert ':type first: ' in d.docs['out']['raw']
        assert ':type second: ' in d.docs['out']['raw']
        assert ':type third: ' in d.docs['out']['raw']

    def test_generating_numpy_docs_params_type_stubs(self):
        doc = self.mynumpydocs
        d = docs.DocString(self.myelem, '    ', doc, type_stub=True, output_style= "reST")
        d.parse_docs()
        d.generate_docs()
        assert ':type second: ' in d.docs['out']['raw']

    def test_no_param(self):
        elem = "    def noparam():"
        doc = """        '''the no param docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        assert not d.docs['out']['params']

    def test_one_line_docs(self):
        elem = "    def oneline(self):"
        doc = """        '''the one line docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc', first_line=True)
        d.parse_docs()
        d.generate_docs()
        assert d.docs['out']['raw'].count('\n') == 0
