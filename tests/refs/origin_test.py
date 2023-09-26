#!/usr/bin/python

import unittest

def my_func_full(first, second=None, third="value"):
    """This is a description of a method.
    It is on several lines.
    Several styles exists:
      -javadoc,
      -reST,
      -groups.
    It uses the javadoc style.

    @param first: the 1st argument.
    with multiple lines
    @type first: str
    @param second: the 2nd argument.
    @return: the result value
    @rtype: int
    @raise KeyError: raises an exception

    """
    print ("this is the code of my full func")

def my_func_multiline_elem(first,
                           second,
                           third=""):
    '''multiline'''
    print ("this has elems in several lines")

def my_func_empty_params(first, second=None, third="value"):
    print ("this is the code of my empty func")

def my_func_empty_no_params():
    print ("this is the code of my empty func no params")

def my_func_desc_lines_params(first, second=None, third="value"):
    '''This is a description but params not described.
    And a new line!
    '''
    print ("this is the code of my func")

def my_func_desc_line_params(first, second=None, third="value"):
    '''This is a description but params not described.
    '''
    print ("this is the code of my func")
 
def my_func_desc_line_no_params():
    '''This is a description but no params.
    '''
    print ("this is the code of my func")


def my_func_groups_style(first, second=None, third="value"):
    '''My desc of groups style.

    Parameters:
      first: the first param
      second: the 2nd param
      third: the 3rd param

    '''
    print("group style!")


class MyTestClass(object):

    def __init__(self, one_param=None):
        '''The init with one param

        @param one_param:
        '''
        self.param = one_param
        print("init")

    @classmethod
    def my_cls_method(cls):
        print("cls method")

    def my_method_no_param(self):
        """Do something
        perhaps!
        """
        print("or not")

    def my_method_params_no_docs(self, first, second=None, third="value"):
        print("method params no docs")

    def my_method_multiline_shift_elem(self, first,
                                             second,
                                             third="",
                                             **kwargs):
        '''there are multilines, shift and kwargs'''
        print ("this has elems in several lines")

    def my_method_full(self, first, second=None, third="value"):
        '''The desctiption of method with 3 params and return value
        on several lines

        @param first: the 1st param
        @type first: int
        @param second: the 2nd param with default at None
        @type first: tuple
        @param third: the 3rd param
        @type third: str
        @return: the value
        @rtype: str
        @raise KeyError: key exception

        '''
        print("method full")
        return third


