#!/usr/bin/python

import shutil
import os
import pyment.pyment as pym

CURRENT_DIR = os.path.dirname(__file__)
def absdir(f):
    return os.path.join(CURRENT_DIR, f)


class TestDocStrings:

    def setup_class(self):

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
                @raise KeyError: raises exception

                """'''



        self.inifile = absdir('refs/origin_test.py')
        self.jvdfile = absdir('refs/javadoc_test.py')
        self.rstfile = absdir('refs/rest_test.py')
        self.foo = absdir("refs/foo")

        # prepare test file
        txt = ""
        shutil.copyfile(self.inifile, self.jvdfile)
        with open(self.jvdfile, 'r') as fs:
            txt = fs.read()
        txt = txt.replace("@return", ":returns")
        txt = txt.replace("@raise", ":raises")
        txt = txt.replace("@", ":")
        with open(self.rstfile, 'w') as ft:
            ft.write(txt)
        with open(self.foo, "w") as fooo:
            fooo.write("foo")
        print("setup")

    def teardown_class(self):
        os.remove(self.jvdfile)
        os.remove(self.rstfile)
        os.remove(self.foo)
        print("end")

    def test_parsed_javadoc(self):
        p = pym.PyComment(self.inifile)
        p._parse()
        assert p.parsed

    def test_same_out_javadoc_reST(self):
        pj = pym.PyComment(self.jvdfile)
        pr = pym.PyComment(self.rstfile)
        pj._parse()
        pr._parse()
        assert pj.get_output_docs() == pr.get_output_docs()

    def test_multi_lines_elements(self):
        p = pym.PyComment(self.inifile)
        p._parse()
        assert 'first' in p.get_output_docs()[1]
        assert 'second' in p.get_output_docs()[1]
        assert 'third' in p.get_output_docs()[1]
        assert 'multiline' in p.get_output_docs()[1]

    def test_multi_lines_shift_elements(self):
        p = pym.PyComment(self.inifile)
        p._parse()
        #TODO: improve this test
        assert (len(p.get_output_docs()[13])-len(p.get_output_docs()[13].lstrip())) == 8
        assert 'first' in p.get_output_docs()[13]
        assert 'second' in p.get_output_docs()[13]
        assert 'third' in p.get_output_docs()[13]
        assert 'multiline' in p.get_output_docs()[13]

    def test_windows_rename(self):
        bar = absdir("bar")
        with open(bar, "w") as fbar:
            fbar.write("bar")
        p = pym.PyComment(self.foo)
        p._windows_rename(bar)
        assert not os.path.isfile(bar)
        assert os.path.isfile(self.foo)
        with open(self.foo, "r") as fooo:
            foo_txt = fooo.read()
        assert foo_txt == "bar"

