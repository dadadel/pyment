
class DocString(object):
    '''This class represents the docstring'''
    
    options_dox = ['@param', '@type', '@return', '@rtype']
    def __init__(self, elem_raw=None, docs_raw=None):
        '''
        @param elem_raw: raw data of the element (def or class).
        @param docs_raw: the raw data of the docstring part if any.
        '''
        self.element = {}
        self.element['raw'] = elem_raw
        self.element['name'] = None
        self.element['type'] = None
        self.element['params'] = []
        self.docs = {'in': {}, 'out': {}}
        self.docs['in']['raw'] = docs_raw
        self.docs['in']['desc'] = None
        self.docs['in']['params'] = []
        self.docs['in']['types'] = []
        self.docs['in']['rtype'] = []
        self.docs['out']['raw'] = ''
        self.docs['out']['desc'] = None
        self.docs['out']['params'] = []
        self.docs['out']['types'] = []
        self.docs['out']['rtype'] = []

    def __str__(self):
        txt = "element: " + str(self.element['name']) + ' of type ' + str(self.element['type']) + ':' + str(self.docs['in']['desc']) + '\n'
        txt += '->' + str(self.docs['in']['params']) + '\n'
        return txt

    def __repr__(self):
        return self.__str__()

    def parse_element(self, raw=None):
        '''Parses the element's elements (type, name and parameters) :)
        e.g.: def methode(param1, param2='default')
            def                      -> type
            methode                  -> name
            param1, param2='default' -> parameters

        @param raw: raw data of the element (def or class).

        '''
        if raw is None:
            l = self.element['raw'].strip()
        else:
            l = raw.strip()
        if l.startswith('def ') or l.startswith('class '):
            # retrieves the type
            if l.startswith('def'):
                self.element['type'] = 'def'
                l = l.replace('def ', '')
            else:
                self.element['type'] = 'class'
                l = l.replace('class ', '')
            # retrieves the name
            self.element['name'] = l[:l.find('(')].strip()
            if l[-1] == ':':
                l = l[:-1].strip()
            # retrieves the parameters
            l = l[l.find('(')+1: l.find(')')].strip()
            lst = [c.strip() for c in l.split(',')]
            for e in lst:
                if '=' in e:
                    k, v = e.split('=', 1)
                    self.element['params'].append((k.strip(), v.strip()))
                else:
                    self.element['params'].append(e);
    
    def _extract_docs_description(self):
        '''Extract main description from docstring'''
        data = self.docs['in']['raw']
        idx = len(data)
        for o in DocString.options_dox:
            if o in data:
                i = data.find(o)
                if i < idx:
                    idx = i
        #TODO get desc if params not dox style
        self.docs['in']['desc'] = data[:idx]

    def _extract_docs_params(self):
        '''Extract parameters description from docstring'''
        data = '\n'.join([d.strip() for d in self.docs['in']['raw'].split('\n')])
        nb_docs_params = data.count('@param')
        nb_params = len(self.element['params'])
        listed = 0
        mentioned = 0
        # no dox params but element has params
        # so check if other form of params
        if nb_docs_params == 0 and nb_params > 0:
            for p in self.element['params']:
                if type(p) is tuple:
                    p = p[0]
                if p in data:
                    mentioned += 1
                if ('\n' + p) in data:
                    if listed == 0:
                        self.docs
                    listed += 1
                    idx = data.find('\n' + p)
                    desc = data[idx + len('\n' + p): data[idx + 1:].find('\n')]
                    #TODO manage multiline desc
                    self.docs['in']['params'].append((p, desc))
        # if params dox
        elif nb_docs_params > 0:
            for d in data.split('\n'):
                if d.startswith('@param'):
                    d = d.replace('@param', '').strip().expandtabs()
                    listed += 1
                    p = d[:d.find(' ')]
                    desc = d[d.find(' '):].strip()
                    self.docs['in']['params'].append((p, desc))

    def parse_docs(self, raw=None):
        if raw is not None:
            self.docs['in']['raw'] = raw
        if self.docs['in']['raw'] is None:
            return
        self._extract_docs_params()
        self._extract_docs_description()


    def proceed(self):
        '''Proceed the raw docstring part if any.
        '''

