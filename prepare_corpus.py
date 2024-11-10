from modified_gensim.gensim.models.doc2vec import TaggedDocument
import numpy as np
from importlib import util
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import sys

from python_tokenizer import tree2ast as python_tree2ast
from java_tokenizer import tree2ast as java_tree2ast
from AST import Function, extract_tokens



def get_if_tree_depth(node):
    depth = int(node.type == "If")
    maxdepth = 0
    todig = node.children()
    if hasattr(node, "get_clauses"):
        todig.extend(node.get_clauses())
    if hasattr(node, "get_else") and not node.get_else() is None:
        todig.append(node.get_else())
    for child in todig:
        childdepth = get_if_tree_depth(child)
        if childdepth > maxdepth:
            maxdepth = childdepth
    return maxdepth + depth

class TraceStrategy:
    def do_if(self, node):
        raise NotImplementedError()
    def nb_loop(self, node):
        raise NotImplementedError()

class SystematicStrategy(TraceStrategy):
    def __init__(self, do_if=True, nb_loop=1):
        self._do_if = do_if
        self._nb_loop = nb_loop
    def do_if(self, node):
        return self._do_if
    def nb_loop(self, node):
        return self._nb_loop

class SmartStrategy(TraceStrategy):
    def __init__(self, k=2):
        self.k = k
        self.ifs = {}
    def do_if(self, node):
        if not node in self.ifs:
            self.ifs[node] = len(self.ifs)%self.k
        do = self.ifs[node] == 0
        self.ifs[node] = (self.ifs[node]+1)%self.k
        return do
    def nb_loop(self, node):
        return (get_if_tree_depth(node)+1)*self.k+1

class RandomStrategy(TraceStrategy):
    def __init__(self, seed=1):
        self.random = np.random.RandomState(seed=seed)

class FullRandomStrategy(RandomStrategy):
    def __init__(self, prob_if=0.5, min_loop=1, max_loop=10, seed=1):
        super().__init__(seed=seed)
        self.prob_if = prob_if
        self.min_loop = min_loop
        self.max_loop = max_loop
    def do_if(self, node):
        return self.random.random() <= self.prob_if
    def nb_loop(self, node):
        return self.random.randint(self.min_loop, self.max_loop+1)

class PseudorandomStrategy(RandomStrategy):
    def __init__(self, prob_if=0.4, prob_if_without_else=0.6, min_loop=1, iter_per_if=3, seed=1):
        super().__init__(seed=seed)
        self.prob_if = prob_if
        self.prob_if_without_else = prob_if_without_else
        self.min_loop = min_loop
        self.iter_per_if = iter_per_if
    def do_if(self, node):
        if (hasattr(node, "get_else") and not node.get_else() is None) or (hasattr(node, "get_clauses") and len(node.get_clauses()) > 0):
            prob = self.prob_if
        else:
            prob = self.prob_if_without_else
        return self.random.random() <= prob
    def nb_loop(self, node):
        depth = get_if_tree_depth(node)
        max_loop = self.min_loop + depth*self.iter_per_if
        return self.random.randint(self.min_loop, max_loop)





class CorpusBuilder:
    def __init__(self, element="token", progrepr="source", cwindow=5,
                 trace_strategy=None, nb_traces=10,
                 anonymize=True, anon_num=False, anon_params=False, anon_comments=True,
                 language=None, parser=None, extract_functions=False,
                 seed=1, verbose=False):
        """
        Parameters
        ----------
        element : str, optional
            The level of elements. Must be either "token" or "instruction".
            The default is "token".
        progrepr : str, optional
            The level of instructions. Must be either "instructions", "source"
            or "trace".
            The default is "source".
        """
        self.verbose = verbose
        self.seed = seed
        
        if language is None and parser is None:
            language = "python"
        self.language = language
        if parser is None:
            parser = self.create_parser()
        self.parser = parser
        self.extract_functions = extract_functions
        
        self.anonymize = anonymize
        self.anon_num = anon_num
        self.anon_params = anon_params
        self.anon_comments = anon_comments
        
        self.element = element
        self.progrepr = progrepr
        self.cwindow = cwindow
        self.trace_strategy = trace_strategy or SmartStrategy(k=2)
        self.nb_traces = nb_traces
    
    def create_parser(self):
        # Language.build_library("build/my-languages.so", ["parsers/tree-sitter-"+language])
        parser = Parser()
        if self.language == "python":
            lang = Language(tspython.language(), "python")
        elif self.language == "java":
            Language.build_library("build/my-languages.so", ["parsers/tree-sitter-java"])
            lang = Language("build/my-languages.so", "java")
        # parser.set_language(Language("build/my-languages.so", language))
        parser.set_language(lang)
        return parser

        
    def compute_artificial_trace(self, tree, nestedMethod=None):
        res = []
        newNestedMethod = nestedMethod
        # print(tree.type, nestedMethod)
        if self.extract_functions and tree.type == "Function":
            if newNestedMethod is None:
                newNestedMethod = False
            else:
                newNestedMethod = True
        hastokens = hasattr(tree, "tokens") and len(tree.tokens()) > 0
        hasclauses = hasattr(tree, "clauses")
        doclausetokens = hasattr(tree, "do_clause_tokens_anyway") and tree.do_clause_tokens_anyway()
        askforroot = hasattr(tree, "ask_for_root_clause") and tree.ask_for_root_clause()
        isloop = tree.type == "Loop"
        haselse = hasattr(tree, "get_else")
        doelseanyway = hasattr(tree, "do_else_anyway") and tree.do_else_anyway()
        doelseateachiter = hasattr(tree, "do_else_at_each_iteration") and tree.do_else_at_each_iteration()
        n = 1
        if askforroot:
            if not self.trace_strategy.do_if(tree):
                if hastokens and doclausetokens:
                    res.append(tree.tokens())
                n = 0
        elif isloop:
            n = self.trace_strategy.nb_loop(tree)
        for _ in range(n):
            if hastokens:
                res.append(tree.tokens())
            for c in tree.children():
                res.extend(self.compute_artificial_trace(c, nestedMethod=newNestedMethod))
            if isloop and doelseateachiter:
                e = tree.get_else()
                if not e is None:
                    res.extend(self.compute_artificial_trace(e, nestedMethod=newNestedMethod))
        didroot = n > 0
        if hasattr(tree, "get_prefix") and not tree.get_prefix() is None:
            res.extend(self.compute_artificial_trace(tree.get_prefix(), nestedMethod=newNestedMethod))
        if hasclauses and (not didroot or not askforroot):
            if not askforroot:
                didroot = False
            clauses = tree.get_clauses()
            if len(clauses) > 0:
                for e in clauses:
                    if not didroot:
                        if self.trace_strategy.do_if(e):
                            res.extend(self.compute_artificial_trace(e, nestedMethod=newNestedMethod))
                            didroot = True
                        elif doclausetokens:
                            tks = e.tokens()
                            if len(tks) > 0:
                                res.append(tks)
        if haselse and (not didroot or doelseanyway):
            e = tree.get_else()
            if not e is None:
                res.extend(self.compute_artificial_trace(e, nestedMethod=newNestedMethod))
        if hasattr(tree, "get_suffix") and not tree.get_suffix() is None:
            res.extend(self.compute_artificial_trace(tree.get_suffix(), nestedMethod=newNestedMethod))
        return res
    
    def get_trace(self, tree):
        """
        Compute the trace of the given tree.

        Parameters
        ----------
        tree : AST
            .

        Returns
        -------
        trace : list of chr.
            The computed trace, as a sequence.
        """
        trace = []
        for it in range(self.nb_traces):
            tr = self.compute_artificial_trace(tree)
            trace.extend(tr)
            if it < self.nb_traces-1:
                trace.extend(["\x00"]*self.cwindow)
        return trace
    
    def tokens2inst(self, tokens):
        return "___".join(tokens).replace(" ","_").replace("___\n","")
    
    def get_doc_names(self, codes=None, test_cases=None, sequences=None, corpus=None):
        if codes is None and sequences is None and corpus is None:
            raise Exception("One of codes, sequences and corpus must be provided")
        if sequences is None:
            if not codes is None:
                sequences = self.build_sequences(codes, test_cases)
            else:
                sequences = [doc.words for doc in corpus]
        
        if self.element == "token":
            res = [self.tokens2inst(sequence) for sequence in sequences]
        elif self.element == "instruction":
            res = [str(i)+"\n".join(sequence) for i,sequence in enumerate(sequences)]
        return res
    
    def ast2sequence(self, ast):
        toexclude = {
            "texts": tuple(),
            "python": tuple(),
            "java": (
                ["{", "}"], ["{", "\n", "}"], ["{"], ["}"],
                # [";"],
                [","],
            )
        }
        insts_tks = []
        if self.progrepr in ("source", "ast"):
            insts_tks = extract_tokens(ast)
        elif self.progrepr == "trace":
            insts_tks = self.get_trace(ast)

        sequence = []
        for inst_tks in insts_tks:
            if len(inst_tks) > 0:
                if self.element == "token":
                    sequence.extend(inst_tks)
                elif self.element == "instruction":
                    if inst_tks[-1] == "\n":
                        inst_tks = inst_tks[:-1]
                    if not inst_tks in toexclude[self.language]:
                        sequence.append("___".join(inst_tks))

        return sequence
    
    def code2asts(self, code):
        tree = self.parser.parse(bytes(code, "utf-8"))
        node = tree.root_node
        
        if self.language == "python":
            ast = python_tree2ast(node, self.element,
                                  anonymize=self.anonymize,
                                  anon_num=self.anon_num,
                                  anon_params=self.anon_params,
                                  anon_comments=self.anon_comments)
        elif self.language == "java":
            ast = java_tree2ast(node, self.element,
                                anonymize=self.anonymize,
                                anon_num=self.anon_num,
                                anon_params=self.anon_params,
                                anon_comments=self.anon_comments)
        else:
            raise Exception("unknown language: {}".format(self.language))

        if self.extract_functions:
            asts = []
            todo = [ast]
            while len(todo) > 0:
                node = todo.pop(0)
                if node.type == "Function":
                    asts.append(node)
                else:
                    for c in node.children():
                        todo.append(c)
                    if hasattr(node, "get_clauses"):
                        for c in node.get_clauses():
                            todo.append(c)
                    if hasattr(node, "get_else"):
                        c = node.get_else()
                        if not c is None:
                            todo.append(node.get_else())
        else:
            asts = [ast]

        return asts
        
    def code2sequences(self, code):
        asts = self.code2asts(code)
        return [self.ast2sequence(ast) for ast in asts]
        
    
    def build_sequences(self, codes, test_cases=None):
        sequences = []
        start = 0
        for icode,code in enumerate(codes[start:]):
            if self.verbose:
                print(icode+start)
            sequences.extend(self.code2sequences(code))
        return sequences
    
    def sequences2corpus(self, sequences, tags=True):
        corpus = [TaggedDocument(sequence, [str(isequence) if tags else "0"])
                  for isequence,sequence in enumerate(sequences)]
        return corpus
    
    def build_corpus(self, codes, test_cases=None, tags=True):
        """
        Builds a corpus of TaggedDocuments from the given codes.

        Parameters
        ----------
        codes : list of str
            The batch of code to build the corpus from.

        Returns
        -------
        corpus : list of TaggedDocument
            The corpus built from the codes.
        """
        sequences = self.build_sequences(codes, test_cases=test_cases)
        return self.sequences2corpus(sequences, tags=tags)
    
    def __getstate__(self):
        state = self.__dict__.copy()
        # Can't pickle parser
        del state["parser"]
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        # Add parser back since it doesn't exist in the pickle
        self.parser = self.create_parser()

