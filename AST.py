#! /usr/bin/python3
# -*- coding: UTF-8 -*-

class Node:
    type = "Node"
    
    def __init__(self):
        self.nodes = []
        self.lns = tuple()
    
    def children(self):
        return self.nodes.copy()
    
    def add_child(self, child):
        self.nodes.append(child)
    
    def linenos(self):
        if len(self.lns) == 0:
            for c in self.nodes:
                self.update_linenos(c.linenos())
        return self.lns
    
    def update_linenos(self, ln):
        if len(self.lns) == 0:
            self.lns = ln
        else:
            if len(ln) == 1:
                ln = (ln[0], ln[0])
            if len(self.lns) == 1:
                self.lns = (self.lns[0], self.lns[0])
            lns = (min(ln[0], self.lns[0]),
                   max(ln[1], self.lns[1]))
            if lns[0] == lns[1]:
                lns = (lns[0],)
            self.lns = lns
    
    def __repr__(self):
        return "block"

class NodeWithTokens(Node):
    type = "NodeWithTokens"
    
    def __init__(self):
        super(NodeWithTokens, self).__init__()
        self.tks = []
    
    def tokens(self):
        return self.tks.copy()
    
    def add(self, tk, ln):
        self.tks.append(tk)
        self.update_linenos(ln)
    
    def pop(self, i):
        return self.tks.pop(i)
    
    def __repr__(self):
        tokens = self.tokens()
        if len(tokens) > 0:
            return '"'+" ".join(self.tokens())+'"'
        else:
            return super(NodeWithTokens, self).__repr__()

class NodeWithElse(NodeWithTokens):
    type = "NodeWithElse"
    
    def __init__(self):
        super(NodeWithElse, self).__init__()
        self.else_clause = None
        self.doelseanyway = False
        self.doelseateachiteration = False
    
    def enable_do_else_anyway(self):
        self.doelseanyway = True
    
    def do_else_anyway(self):
        return self.doelseanyway
    
    def enable_do_else_at_each_iteration(self):
        self.doelseateachiteration = True
    
    def do_else_at_each_iteration(self):
        return self.doelseateachiteration
    
    def get_else(self):
        return self.else_clause
    
    def set_else(self, else_clause):
        if not self.else_clause is None:
            raise Exception("This node already has an else clause!")
        self.else_clause = else_clause
    
    def reset_else(self):
        self.else_clause = None
        
    def linenos(self):
        if len(self.lns) == 0:
            super(NodeWithElse, self).linenos()
            if not self.get_else() is None:
                self.update_linenos(self.get_else().linenos())
        return self.lns

class NodeWithClauses(NodeWithElse):
    type = "NodeWithClauses"
    
    def __init__(self):
        super(NodeWithClauses, self).__init__()
        self.clauses = []
        self.doclausetokensanyway = True
        self.askforrootclause = True
        self.prefix = None
        self.suffix = None
    
    def get_clauses(self):
        return self.clauses.copy()
    
    def add_clause(self, clause):
        self.clauses.append(clause)
    
    def disable_do_clause_tokens_anyway(self):
        self.doclausetokensanyway = False
    
    def do_clause_tokens_anyway(self):
        return self.doclausetokensanyway
    
    def disable_ask_for_root_clause(self):
        self.askforrootclause = False
    
    def ask_for_root_clause(self):
        return self.askforrootclause
    
    def get_prefix(self):
        return self.prefix
    def set_prefix(self, prefix):
        self.prefix = prefix
    def get_suffix(self):
        return self.suffix
    def set_suffix(self, suffix):
        self.suffix = suffix
    
    def linenos(self):
        if len(self.lns) == 0:
            super(NodeWithClauses, self).linenos()
            for c in self.get_elifs():
                self.update_linenos(c.linenos())
        return self.lns

class Program(Node):
    type = "Program"

class Class(NodeWithTokens):
    type = "Class"

class Function(NodeWithTokens):
    type = "Function"
    
    def __init__(self):
        super(Function, self).__init__()
        self.name = None
    
    def set_name(self, name):
        self.name = name
    
    def get_name(self):
        if self.name is None:
            raise Exception("This node has not received a name yet!")
        return self.name

class Instruction(NodeWithTokens):
    type = "Instruction"

class Loop(NodeWithElse):
    type = "Loop"

class If(NodeWithClauses):
    type = "If"

class Try(NodeWithClauses):
    type = "Try"
    
    def __init__(self):
        super(Try, self).__init__()
        self.enable_do_else_anyway()
        self.disable_do_clause_tokens_anyway()
        self.disable_ask_for_root_clause()

class Switch(NodeWithClauses):
    type = "Switch"
    
    def __init__(self):
        super(Switch, self).__init__()
        self.disable_ask_for_root_clause()

def extract_tokens(tree):
    insts_tks = []
    last_c = None
    if hasattr(tree, "tokens"):
        if len(tree.tokens()) > 0:
            insts_tks.append(tree.tokens())
        last_c = tree
    for c in tree.children():
        while len(c.linenos()) == 0 and len(c.children()) > 0:
            c = c.children()[0]
        if len(c.linenos()) > 0:
            if not last_c is None and c.linenos()[0] > last_c.linenos()[-1] and not insts_tks[-1][-1] in ("\n","\\\n"):
                insts_tks[-1].append("\n")
            last_c = c
        tks = extract_tokens(c)
        if len(tks) > 0:
            insts_tks.extend(tks)
    if hasattr(tree, "get_prefix") and not tree.get_prefix() is None:
        c = tree.get_prefix()
        while len(c.linenos()) == 0 and len(c.children()) > 0:
            c = c.children()[0]
        if len(c.linenos()) > 0:
            if not last_c is None and len(c.linenos()) > 0 and c.linenos()[0] > last_c.linenos()[-1] and not insts_tks[-1][-1] in ("\n","\\\n"):
                insts_tks[-1].append("\n")
            last_c = c
        tks = extract_tokens(tree.get_prefix())
        if len(tks) > 0:
            insts_tks.extend(tks)
    if hasattr(tree, "get_clauses"):
        for c in tree.get_clauses():
            while len(c.linenos()) == 0 and len(c.children()) > 0:
                c = c.children()[0]
            if len(c.linenos()) > 0:
                if not last_c is None and len(c.linenos()) > 0 and c.linenos()[0] > last_c.linenos()[-1] and not insts_tks[-1][-1] in ("\n","\\\n"):
                    insts_tks[-1].append("\n")
                last_c = c
            tks = extract_tokens(c)
            if len(tks) > 0:
                insts_tks.extend(tks)
    if hasattr(tree, "get_else"):
        c = tree.get_else()
        if not c is None:
            while len(c.linenos()) == 0 and len(c.children()) > 0:
                c = c.children()[0]
            if len(c.linenos()) > 0:
                if not last_c is None and len(c.linenos()) > 0 and c.linenos()[0] > last_c.linenos()[-1] and not insts_tks[-1][-1] in ("\n","\\\n"):
                    insts_tks[-1].append("\n")
            tks = extract_tokens(tree.get_else())
            if len(tks) > 0:
                insts_tks.extend(tks)
    if hasattr(tree, "get_suffix") and not tree.get_suffix() is None:
        c = tree.get_suffix()
        while len(c.linenos()) == 0 and len(c.children()) > 0:
            c = c.children()[0]
        if len(c.linenos()) > 0:
            if not last_c is None and len(c.linenos()) > 0 and c.linenos()[0] > last_c.linenos()[-1] and not insts_tks[-1][-1] in ("\n","\\\n"):
                insts_tks[-1].append("\n")
            last_c = c
        tks = extract_tokens(tree.get_suffix())
        if len(tks) > 0:
            insts_tks.extend(tks)
    return insts_tks

def display(tree, indent=""):
    res = [indent+str(tree)]
    for c in tree.children():
        res.append(display(c, indent=indent+"\t"))
    if hasattr(tree, "get_prefix") and not tree.get_prefix() is None:
        res.append(display(tree.get_prefix(), indent=indent))
    if hasattr(tree, "get_clauses"):
        if len(tree.get_clauses()) > 0:
            res.append(indent+"\tclauses:")
            for c in tree.get_clauses():
                res.append(display(c, indent=indent+"\t\t"))
    if hasattr(tree, "get_else") and not tree.get_else() is None:
        res.append(indent+"\telse:")
        res.append(display(tree.get_else(), indent=indent+"\t\t"))
    if hasattr(tree, "get_suffix") and not tree.get_suffix() is None:
        res.append(display(tree.get_suffix(), indent=indent))
    return "\n".join(res)
