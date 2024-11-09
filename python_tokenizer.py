#! /usr/bin/python3
# -*- coding: UTF-8 -*-

import builtins
import keyword
from AST import Program, Class, Function, Instruction, Loop, If, Try

def check_module(module):
    try:
        exec("import {}".format(module))
        return True
    except:
        return False

def check_imports(base, tool, module=None):
    try:
        if module is None:
            # print("from {} import {}".format(base, tool))
            exec("from {} import {}".format(base, tool))
            # print("\toui")
        else:
            # print("from {}.{} import {}".format(module, base, tool))
            exec("from {}.{} import {}".format(module, base, tool))
            # print("\toui")
        return True
    except:
        # print("\tnon")
        return False

def is_fun(fname):
    for t in (list, tuple, dict, set, int, bool, float, str, complex):
        if hasattr(t, fname):
            return True
    from _io import TextIOWrapper
    if hasattr(TextIOWrapper, fname):
        return True
    if hasattr(is_fun, fname):
        return True
    if hasattr((_ for _ in []), fname):
        return True
    if hasattr(filter(None, []), fname):
        return True
    if hasattr(map(None, []), fname):
        return True
    return False



def get_linenos(nodes):
    lns = [None, None]
    for node in nodes:
        start = node.start_point[0]
        if lns[0] is None or start < lns[0]:
            lns[0] = start
        end = node.end_point[0]
        if lns[1] is None or end > lns[1]:
            lns[1] = end
    if lns[0] == lns[1]:
        lns = (lns[0],)
    return tuple(lns)

def anonymize_id(node, names, pattern, anon_num):
    tree = Instruction()
    name = node.text.decode("utf-8")
    target = pattern
    if anon_num:
        cpt = 1
        for e in names:
            if any([pattern in c for c in names[e]]):
                cpt += 1
        target += str(cpt)
    names[name] = ["___"+target+"___"]
    for tk in names[name]:
        add_token_to_tree(node, tree, tk=tk)
    return tree

def anonymize_var(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if anonymize:
        tr = anonymize_id(node, names, "VAR", anon_num)
        combine_trees(tree, tr)
    else:
        add_token_to_tree(node, tree)
    return tree

def anonymize_param(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if anonymize:
        if anon_params:
            pattern = "PARAM"
        else:
            pattern = "VAR"
        tr = anonymize_id(node, names, pattern, anon_num)
        combine_trees(tree, tr)
    else:
        add_token_to_tree(node, tree)
    return tree

def anonymize_func_name(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    name = node.text.decode("utf-8")
    if anonymize:
        if name == "__init__":
            pattern = "CONSTRUCTOR"
        else:
            pattern = "MAIN_FUNCTION"
        tr = anonymize_id(node, names, pattern, False)
        combine_trees(tree, tr)
    else:
        add_token_to_tree(node, tree)
    return tree

def anonymize_class_name(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if anonymize:
        tr = anonymize_id(node, names, "MAIN_CLASS", False)
        combine_trees(tree, tr)
    else:
        add_token_to_tree(node, tree)
    return tree

def anonymize_const(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if anonymize:
        if node.type == "integer":
            if node.text.decode("utf-8")[-1] in ("j", "J"):
                tk = "___CONST_COMPLEX___"
            else:
                tk = "___CONST_INT___"
        elif node.type == "float":
            tk = "___CONST_FLOAT___"
        elif node.type in ("string", "concatenated_string"):
            tk = "___CONST_STRING___"
        elif node.type in ("true", "false"):
            tk = "___CONST_BOOL___"
        elif node.type == "none":
            tk = "___CONST_NONE___"
        else:
            raise Exception("unknown constant: {}".format(node.type))
    else:
        tk = node.text.decode("utf-8")
    add_token_to_tree(node, tree, tk=tk)
    return tree

def anonymize_comment(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if anonymize and anon_comments:
        tk = "___COMMENT___"
    else:
        tk = node.text.decode("utf-8")
    comment = Instruction()
    add_token_to_tree(node, comment, tk=tk)
    tree.add_child(comment)
    return tree

def is_in_import_from(node, import_from):
    tool = node.text.decode("utf-8")
    for imp in import_from:
        if tool in import_from[imp]:
            return True
        if "*" in import_from[imp] and check_imports(imp, tool):
            return True
    return False

def tokenize_identifier(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                               check_builtins=True, force_var=False, is_func_name=False):
    tree = Instruction()
    
    name = node.text.decode("utf-8")
    if force_var:
        if name in names and any(["VAR" in c or "PARAM" in c for c in names[name]]):
            for tk in names[name]:
                add_token_to_tree(node, tree, tk=tk)
        else:
            tr = anonymize_var(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    elif is_func_name:
        if is_fun(name) or (check_builtins and name in dir(builtins)) or (is_in_import_from(node, import_from)):
            add_token_to_tree(node, tree, tk=name)
        else:
            names[name] = ["___FUNCTION_NAME___"]
            for tk in names[name]:
                add_token_to_tree(node, tree, tk=tk)
    elif name in names:
        for tk in names[name]:
            add_token_to_tree(node, tree, tk=tk)
    elif (check_builtins and name in dir(builtins)) or (is_in_import_from(node, import_from)):
        add_token_to_tree(node, tree, tk=name)
    else:
        tr = anonymize_var(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    
    return tree

def tokenize_pattern(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                            force_var=True):
    tree = Instruction()
    
    ln = get_linenos([node])
    line = ln[0]
    for c in node.children:
        if c.start_point[0] > line:
            add_token_to_tree(c, tree, tk="\n")
            line = c.start_point[0]
        
        if c.type in (",", "(", ")", "[", "]"):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                             force_var=force_var)
            combine_trees(tree, tr)
        elif c.type in ("pattern_list", "list_pattern", "tuple_pattern"):
            tr = tokenize_pattern(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                          force_var=force_var)
            combine_trees(tree, tr)
        elif c.type == "subscript":
            tr = tokenize_subscript(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "line_continuation":
            add_token_to_tree(c, tree, tk="\\\n")
        elif c.type == "attribute":
            tr = tokenize_attribute(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown pattern list element type: {}".format(c.type))
    
    return tree

def tokenize_intern_node(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                         nested=False):
    tree = Instruction()
    for c in node.children:
        tr = tokenize_node(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        if nested:
            tree.add_child(tr)
        else:
            combine_trees(tree, tr)
    return tree

def tokenize_as_pattern(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    value = node.children[0]
    tr = tokenize_expr(value, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
    combine_trees(tree, tr)
    
    for c in node.children[1:-1]:
        if c.type == "as":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    children = node.children[-1].children
    for i,c in enumerate(children):
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                             force_var=i==len(children)-1)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown as pattern target type: {}".format(c.type))
    
    return tree

def tokenize_with_clause(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children[0].children:
        if c.type == "as_pattern":
            tr = tokenize_as_pattern(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_default_parameter(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            tr = anonymize_param(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "=":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_typed_parameter(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            tr = anonymize_param(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == ":":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_parameters(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    ln = get_linenos([node])
    line = ln[0]
    nbid = 0
    for c in node.children:
        if c.start_point[0] > line:
            add_token_to_tree(c, tree, tk="\n")
            line = c.start_point[0]
        
        if c.type in (",", "(", ")"):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            name = c.text.decode("utf-8")
            if nbid == 0 and name == "self":
                add_token_to_tree(c, tree)
            else:
                tr = anonymize_param(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            nbid += 1
        elif c.type == "default_parameter":
            tr = tokenize_default_parameter(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "typed_parameter":
            tr = tokenize_typed_parameter(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_block_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    suffix_clauses = ("block", "elif_clause", "else_clause", "except_clause")
    for c in node.children:
        if keyword.iskeyword(c.type) or c.type in (":", "->"):
            add_token_to_tree(c, tree)
        elif c.type in ("comparison_operator", "boolean_operator"):
            tr = tokenize_operator_expression(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "call":
            tr = tokenize_call(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "with_clause":
            tr = tokenize_with_clause(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "parameters":
            tr = tokenize_parameters(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "expression_list":
            tr = tokenize_expr_list(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "parenthesized_expression":
            tr = tokenize_parenthesized_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "comment":
            tr = anonymize_comment(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "not_operator":
            tr = tokenize_operator_expression(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in suffix_clauses:
            pass
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_operator_expression(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("<", ">", "<=", ">=", "==", "!=", "<>",
                      "&", "|", "^", "and", "or", "not", "is", "in",
                      "-", "+", "/", "//", "*", "**", "%", "<<", ">>"):
            tk = c.type
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "is not":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_struct(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    if node.type == "dictionary":
        const_name = "___CONST_DICT___"
    elif node.type == "set":
        const_name = "___CONST_SET___"
    elif node.type == "list":
        const_name = "___CONST_LIST___"
    elif node.type == "tuple":
        const_name = "___CONST_TUPLE___"
    else:
        raise Exception("unknown structure type: {}".format(node.type))
    
    if anonymize and not contains_identifier(node):
        add_token_to_tree(node, tree, tk=const_name)
    else:
        for c in node.children:
            if c.type in (",", "(", ")", "[", "]", "{", "}"):
                add_token_to_tree(c, tree)
            elif c.type == "pair":
                tr = tokenize_pair(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            else:
                tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
    
    return tree

def tokenize_for_in_clause(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("for", "in"):
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_pair(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == ":":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_struct_comprehension(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    if node.type == "dictionary_comprehension":
        const_name = "___CONST_DICT___"
    elif node.type == "set_comprehension":
        const_name = "___CONST_SET___"
    elif node.type == "list_comprehension":
        const_name = "___CONST_LIST___"
    elif node.type == "generator_expression":
        const_name = "___CONST_GENERATOR___"
    else:
        raise Exception("unknown comprehension structure type: {}".format(node.type))
    
    for i in range(len(node.children)):
        if node.children[i].type == "for_in_clause":
            break
    if node.children[i].type != "for_in_clause":
        raise Exception("unknown struct comprehension format: {}".format([c.type for c in node.children]))
    
    for j in range(len(node.children[i].children)):
        if node.children[i].children[j].type == "in":
            break
    if node.children[i].children[j].type != "in":
        raise Exception("unknown for-in clause format: {}".format([c.type for c in node.children[i].children]))
    
    if anonymize and all([not contains_identifier(c) for c in node.children[i].children[j:]]):
        add_token_to_tree(node, tree, tk=const_name)
    else:
        targets = None
        for c in node.children[i].children[1:j]:
            if c.type == "identifier":
                targets = [c.text.decode("utf-8")]
            elif c.type in ("pattern_list", "tuple_pattern"):
                targets = [cc.text.decode("utf-8") for cc in c.children if cc.type == "identifier"]
        if targets is None:
            raise Exception("unknown for in clause pattern vars: {}".format([c.type for c in node.children[i].children[1:j]]))
        
        values_formats = ("identifier", "pair", "binary_operator")
        ids = []
        for c in node.children[:i]:
            if c.type in values_formats:
                ids.extend(get_identifiers(c))
        if anonymize and all([e in targets for e in ids]) and all([not contains_identifier(c) for c in node.children[i].children[j:]]):
            add_token_to_tree(node, tree, tk=const_name)
        else:
            for c in node.children[i].children[:j]:
                if c.type == "identifier":
                    tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                        force_var=True)
                elif c.type == "pattern_list":
                    tokenize_pattern(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                     force_var=True)
            for c in node.children:
                if c.type in ("(", ")", "[", "]", "{", "}"):
                    add_token_to_tree(c, tree)
                elif c.type == "for_in_clause":
                    tr = tokenize_for_in_clause(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                    combine_trees(tree, tr)
                elif c.type == "pair":
                    tr = tokenize_pair(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                    combine_trees(tree, tr)
                elif c.type == "if_clause":
                    tr = tokenize_conditional_expression(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                    combine_trees(tree, tr)
                else:
                    tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                    combine_trees(tree, tr)
    
    return tree

def tokenize_argument_list(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    ln = get_linenos([node])
    line = ln[0]
    for c in node.children:
        if c.start_point[0] > line:
            add_token_to_tree(c, tree, tk="\n")
            line = c.start_point[0]
        
        if c.type in (",", "(", ")"):
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def is_imported(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tks = node.children[0].text.decode("utf-8").replace("\\\n", "").split(".")
    cumul = ""
    for tk in tks:
        if len(cumul) > 0:
            cumul += "."
        cumul += tk
        if cumul in imports:
            return True
        for module in import_from:
            if cumul in import_from[module] or ("*" in import_from[module] and check_imports(module, cumul)):
                return True
    return False

def tokenize_imported_attribute(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    ids = node.text.decode("utf-8").replace("\\\n", "").split(".")
    base = ""
    i = 0
    found = None
    while i < len(ids) and found is None:
        if len(base) > 0:
            base += "."
        base += ids[i]
        if base in imports:
            found = "imports"
        if base in import_from:
            found = "import_from"
        for module in import_from:
            if base in import_from[module]:
                found = "import_from "+module
            elif ("*" in import_from[module] and check_imports(module, base)):
                found = "import_from * "+module
        i += 1
    
    if found is None:
        raise Exception("unknown attribute importation")
    else:
        ibreaks = {}
        nbpoints = 0
        for ic,c in enumerate(node.children):
            if c.type == ".":
                nbpoints += 1
            elif c.type == "line_continuation":
                ibreaks[ic-len(ibreaks)-nbpoints] = node.children[ic-1].type == "."
        
        for j,name in enumerate(ids[:i]):
            if len(tree.tokens()) > 0:
                add_token_to_tree(node, tree, tk=".")
            
            if j in ibreaks and ibreaks[j]:
                add_token_to_tree(node, tree, tk="\\\n")
            
            if name in names:
                for tk in names[name]:
                    add_token_to_tree(node, tree, tk=tk)
            else:
                add_token_to_tree(node, tree, tk=name)
            
            if j in ibreaks and not ibreaks[j]:
                add_token_to_tree(node, tree, tk="\\\n")
        
        if base in names:
            base = "".join(names[base])
        if found[:12] == "import_from ":
            if found[:14] == "import_from * ":
                module = found[14:]
            elif found[:12] == "import_from ":
                module = found[12:]
            base = module+"."+base
        
        for name in ids[i:]:
            add_token_to_tree(node, tree, tk=".")
            if check_imports(base, name):
                add_token_to_tree(node, tree, tk=name)
            else:
                add_token_to_tree(node, tree, tk="___TOOL___")
            base += "."+name
    
    return tree

def tokenize_normal_attribute(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for i,c in enumerate(node.children):
        if c.type == ".":
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            name = c.text.decode("utf-8")
            if name in names:
                for tk in names[name]:
                    add_token_to_tree(c, tree, tk=tk)
            elif is_fun(name):
                add_token_to_tree(node, tree, tk=name)
            else:
                tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
        elif c.type == "subscript":
            tr = tokenize_subscript(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "attribute":
            tr = tokenize_attribute(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)

    return tree

def tokenize_attribute(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if is_imported(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
        tr = tokenize_imported_attribute(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        tr = tokenize_normal_attribute(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    return tree

def anonymize_tool(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                   module):
    tree = Instruction()
    name = node.text.decode("utf-8")
    if check_imports(module, name):
        if name in names:
            names.pop(name)
        add_token_to_tree(node, tree, tk=name)
    else:
        tr = anonymize_id(node, names, "TOOL", False)
        combine_trees(tree, tr)
    return tree

def tokenize_dotted_name(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                         module):
    tree = Instruction()
    
    for c in node.children:
        if c.type in (",", "."):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = anonymize_tool(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                 module)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown dotted name operand type: {}".format(c.type))
    
    return tree

def tokenize_modules(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                     isfromed=False, isaliased=False):
    tree = Instruction()
    
    module = ""
    for i,c in enumerate(node.children):
        if c.type == ".":
            add_token_to_tree(c, tree)
            module += "."
        elif c.type == "identifier":
            name = c.text.decode("utf-8")
            module += name
            if check_module(module):
                add_token_to_tree(c, tree, tk=name)
            else:
                if i == 0:
                    pattern = "MODULE"
                else:
                    pattern = "TOOL"
                tr = anonymize_id(c, names, pattern, False)
                combine_trees(tree, tr)
        elif c.type == "line_continuation":
            add_token_to_tree(c, tree, tk="\\\n")
        else:
            raise Exception("unknown modules operand type: {}".format(c.type))
    if not isfromed and not isaliased:
        imports.append(module)
    return tree

def tokenize_aliased_from_import(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                 module):
    tree = Instruction()
    
    for c in node.children:
        if c.type == "dotted_name":
            name = c.children[0].text.decode("utf-8")
            if check_imports(module, name):
                tk = name
            else:
                tk = "___TOOL___"
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "identifier":
            name = c.text.decode("utf-8")
            names[name] = [tk]
            import_from[module] = name
            tk = "___TOOL_NAME___"
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "as":
            add_token_to_tree(c, tree)
        elif c.type == "line_continuation":
            add_token_to_tree(c, tree, tk="\\\n")
        else:
            raise Exception("unknown aliased from import operand type: {}".format(c.type))
    
    return tree

def tokenize_aliased_import(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type == "dotted_name":
            tr = tokenize_modules(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                  isaliased=True)
            combine_trees(tree, tr)
            module = [tk for tk in tr.tokens()]
        elif c.type == "identifier":
            name = c.text.decode("utf-8")
            names[name] = module
            imports.append(name)
            if len(module) == 1:
                tk = "___MODULE_NAME___"
            else:
                tk = "___TOOL_NAME___"
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "as":
            add_token_to_tree(c, tree)
        elif c.type == "line_continuation":
            add_token_to_tree(c, tree, tk="\\\n")
        else:
            raise Exception("unknown aliased import operand type: {}".format(c.type))
    
    return tree

def tokenize_import_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    add_token_to_tree(node.children[0], tree)
    for c in node.children[1:]:
        if c.type == ",":
            add_token_to_tree(c, tree)
        elif c.type == "dotted_name":
            tr = tokenize_modules(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "aliased_import":
            tr = tokenize_aliased_import(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "line_continuation":
            add_token_to_tree(c, tree, tk="\\\n")
        else:
            raise Exception("unknown import statement operand type: {}".format(c.type))
    
    return tree

def tokenize_import_from_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    iid = 0
    for c in node.children:
        if c.type in ("from", "import", ",", "__future__"):
            add_token_to_tree(c, tree)
        elif c.type in ("dotted_name", "identifier"):
            if iid == 0:
                tr = tokenize_modules(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                      isfromed=True)
                combine_trees(tree, tr)
                module = "".join([tk for tk in tr.tokens()])
                if not module in import_from:
                    import_from[module] = []
            else:
                if c.type == "dotted_name":
                    tr = tokenize_dotted_name(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                              module=module)
                    combine_trees(tree, tr)
                else:
                    tr = anonymize_tool(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                        module=module)
                    combine_trees(tree, tr)
                tool = "".join([tk for tk in tr.tokens()])
                import_from[module].append(tool)
            iid += 1
        elif c.type == "wildcard_import":
            import_from[module].append("*")
            add_token_to_tree(c, tree)
        elif c.type == "aliased_import":
            tr = tokenize_aliased_from_import(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                              module)
            combine_trees(tree, tr)
        elif c.type == "line_continuation":
            add_token_to_tree(c, tree, tk="\\\n")
        else:
            raise Exception("unknown import from statement operand type: {}".format(c.type))
    
    return tree

def tokenize_blocked_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    auxnames = names
    if node.type == "if_statement":
        tree = If()
    elif node.type in ("for_statement", "while_statement"):
        tree = Loop()
        tree.enable_do_else_anyway()
    elif node.type in ("function_definition", "class_definition"):
        isfun = node.type == "function_definition"
        if isfun:
            tree = Function()
        else:
            tree = Class()
        for i in range(len(node.children)):
            if node.children[i].type == "identifier":
                break
        if node.children[i].type != "identifier":
            raise Exception("unknown function definition format: {}".format([c.type for c in node.children]))
        if isfun:
            name = node.children[i].text.decode("utf-8")
            tree.set_name(name)
            anonymize_func_name(node.children[i], names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        else:
            anonymize_class_name(node.children[i], names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        auxnames = names.copy()
    elif node.type == "try_statement":
        tree = Try()
    else:
        tree = Instruction()
    
    tr = tokenize_block_statement(node, auxnames, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
    combine_trees(tree, tr)
    for c in node.children:
        if c.type == "block":
            tr = tokenize_intern_node(c, auxnames, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                      nested=True)
            combine_trees(tree, tr)
        elif c.type in ("elif_clause", "else_clause", "except_clause"):
            tr = tokenize_block_statement(c, auxnames, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            if c.type == "else_clause":
                tree.set_else(tr)
            else:
                tree.add_clause(tr)
            for cc in c.children:
                if cc.type == "block":
                    trr = tokenize_intern_node(cc, auxnames, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                               nested=True)
                    combine_trees(tr, trr)
    
    return tree

def tokenize_call(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    builtins_exceptions = ("open", "range", "sum", "min", "max", "pow",
                           "len", "print", "abs", "input", "type",
                           "sorted", "reversed", "ord", "chr",
                           "locals", "globals", "map", "zip",
                           "exit")
    
    fun = node.children[0].text.decode("utf-8")
    if anonymize and not contains_identifier(node.children[-1]) and fun in dir(builtins) and not fun in builtins_exceptions and fun[-5:] != "Error" and fun[-9:] != "Exception":
        if fun == "dict":
            tk = "___CONST_DICT___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun == "list":
            tk = "___CONST_LIST___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun == "tuple":
            tk = "___CONST_TUPLE___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun == "set":
            tk = "___CONST_SET___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun == "str":
            tk = "___CONST_STRING___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun=="int":
            tk = "___CONST_INT___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun=="float":
            tk = "___CONST_FLOAT___"
            add_token_to_tree(node, tree, tk=tk)
        elif fun=="bool":
            tk = "___CONST_BOOL___"
            add_token_to_tree(node, tree, tk=tk)
        else:
            print(node.parent.parent.text)
            raise Exception("unknown builtins function: {}".format(fun))
    else:
        if not fun in names:
            tokenize_identifier(node.children[0], names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                       is_func_name=True)
        for c in node.children:
            if c.type == "identifier":
                tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "attribute":
                tr = tokenize_attribute(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in ("(", ")"):
                add_token_to_tree(c, tree)
            elif c.type == "argument_list":
                tr = tokenize_argument_list(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "subscript":
                tr = tokenize_subscript(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            else:
                tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
    
    return tree

def tokenize_expr_list(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type == ",":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_parenthesized_expr(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("(", ")"):
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_assert_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in ("assert", ","):
            add_token_to_tree(c, tree)
        elif c.type == "string":
            tr = anonymize_const(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_raise_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "raise":
            add_token_to_tree(c, tree)
        elif c.type == "call":
            tr = tokenize_call(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_global_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "global":
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_expr(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    if node.type == "function_definition":
        tree = Function()
    else:
        tree = Instruction()
    
    if node.type == "identifier":
        tr = tokenize_identifier(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in (";", "not in", ":", ",", "[", "]"):
        add_token_to_tree(node, tree)
    elif node.type in ("type", "generic_type", "type_parameter"):
        tr = tokenize_expr(node.children[0], names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("integer", "float", "string", "true", "false", "none", "concatenated_string"):
        tr = anonymize_const(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("tuple", "list", "dictionary", "set"):
        tr = tokenize_struct(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("dictionary_comprehension", "set_comprehension", "list_comprehension", "generator_expression"):
        tr = tokenize_struct_comprehension(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("binary_operator", "comparison_operator", "boolean_operator"):
        tr = tokenize_operator_expression(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "not_operator":
        tr = tokenize_operator_expression(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "call":
        tr = tokenize_call(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "expression_list":
        tr = tokenize_expr_list(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "lambda":
        tr = tokenize_lambda(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "line_continuation":
        add_token_to_tree(node, tree, tk="\\\n")
    elif node.type == "subscript":
        tr = tokenize_subscript(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "unary_operator":
        tr = tokenize_operator_expression(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "parenthesized_expression":
        tr = tokenize_parenthesized_expr(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "assert_statement":
        tr = tokenize_assert_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "raise_statement":
        tr = tokenize_raise_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "as_pattern":
        tr = tokenize_as_pattern(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("if_statement", "while_statement", "for_statement", "with_statement", "function_definition"):
        tr = tokenize_blocked_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "global_statement":
        tr = tokenize_global_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("pattern_list", "list_pattern", "tuple_pattern"):
        tr = tokenize_pattern(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "assignment":
        tr = tokenize_assignment(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "attribute":
        tr = tokenize_attribute(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "conditional_expression":
        tr = tokenize_conditional_expression(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "keyword_argument":
        auxnames = names.copy()
        tr = tokenize_default_parameter(node, auxnames, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "delete_statement":
        tr = tokenize_delete_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type in ("list_splat", "dictionary_splat"):
        tr = tokenize_struct_splat(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "ellipsis":
        tk = node.type.capitalize()
        add_token_to_tree(node, tree, tk=tk)
    elif node.type == "argument_list":
        tr = tokenize_argument_list(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "yield":
        tr = tokenize_yield(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "comment":
        tr = anonymize_comment(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        raise Exception("unknown node type: {}".format(node.type))
    
    return tree

def tokenize_yield(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "yield":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_struct_splat(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("*", "**"):
            tk = c.type
            add_token_to_tree(c, tree, tk=tk)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_delete_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "del":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_assignment(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for i,c in enumerate(node.children):
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                      force_var=i==0)
            combine_trees(tree, tr)
        elif c.type in ("pattern_list", "list_pattern", "tuple_pattern"):
            tr = tokenize_pattern(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("=","+=","-=","*=","/=","//=","%=","**=","&=","|=","^=","<<=",">>="):
            tk = c.type
            add_token_to_tree(c, tree, tk=tk)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def contains_identifier(node):
    if node.type == "identifier" and not node.text.decode("utf-8") in dir(builtins) and not node.parent.type == "keyword_argument":
        return True
    else:
        for c in node.children:
            if contains_identifier(c):
                return True
        return False

def get_identifiers(node):
    if node.type == "identifier" and not node.text.decode("utf-8") in dir(builtins):
        return [node.text.decode("utf-8")]
    else:
        res = []
        for c in node.children:
            res.extend(get_identifiers(c))
        return res

def tokenize_slice(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == ":":
            add_token_to_tree(c, tree)
        elif c.type == "subscript":
            tr = tokenize_subscript(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "integer":
            tr = anonymize_const(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_subscript(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    target = node.children[0]
    if target.type == "identifier":
        tr = tokenize_identifier(target, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "subscript":
        tr = tokenize_subscript(target, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        tr = tokenize_expr(target, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    
    if anonymize and not any([contains_identifier(c) for c in node.children[1:]]):
        isslice = False
        for c in node.children[1:]:
            if c.type == "slice":
                isslice = True
        if isslice:
            tk = "___CONST_SLICE___"
        else:
            tk = "___CONST_ACCESS___"
        add_token_to_tree(node, tree, tk=tk)
    else:
        for c in node.children[1:]:
            if c.type == "identifier":
                tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in ("[", "]"):
                add_token_to_tree(c, tree)
            elif c.type == "subscript":
                tr = tokenize_subscript(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "integer":
                tr = anonymize_const(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "slice":
                tr = tokenize_slice(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "binary_operator":
                tr = tokenize_operator_expression(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "call":
                tr = tokenize_call(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "parenthesized_expression":
                tr = tokenize_parenthesized_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            else:
                tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
    
    return tree

def tokenize_conditional_expression(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("if", "else"):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "boolean_operator":
            tr = tokenize_operator_expression(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_simple_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("pass", "break", "continue"):
            add_token_to_tree(c, tree)
        else:
            raise Exception("unknown simple statement type: {}".format(c.type))
    
    return tree

def tokenize_lambda(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    names = names.copy()
    
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("lambda", ":"):
            add_token_to_tree(c, tree)
        elif c.type == "lambda_parameters":
            tr = tokenize_parameters(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_return_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    names = names.copy()
    
    tree = Instruction()
    
    for c in node.children:
        if c.type == "return":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree

def tokenize_program(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Program()
    for c in node.children:
        tree.add_child(tokenize_node(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments))
    return tree

def tokenize_print_statement(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "print":
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree

def tokenize_node(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    funcs = {
        "module": tokenize_program,
        "class_definition": tokenize_blocked_statement,
        "assignment": tokenize_assignment,
        "subscript": tokenize_subscript,
        "conditional_expression": tokenize_conditional_expression,
        "pass_statement": tokenize_simple_statement,
        "break_statement": tokenize_simple_statement,
        "continue_statement": tokenize_simple_statement,
        "call": tokenize_call,
        "attribute": tokenize_attribute,
        "expression_statement": tokenize_intern_node,
        "augmented_assignment": tokenize_assignment,
        "identifier": tokenize_identifier,
        "lambda": tokenize_lambda,
        "return_statement": tokenize_return_statement,
        "if_statement": tokenize_blocked_statement,
        "while_statement": tokenize_blocked_statement,
        "for_statement": tokenize_blocked_statement,
        "comment": anonymize_comment,
        "string": anonymize_const,
        "import_statement": tokenize_import_statement,
        "import_from_statement": tokenize_import_from_statement,
        "future_import_statement": tokenize_import_from_statement,
        "try_statement": tokenize_blocked_statement,
        "raise_statement": tokenize_raise_statement,
        "assert_statement": tokenize_assert_statement,
        "print_statement": tokenize_print_statement,
    }
    
    if node.type in funcs:
        tree = funcs[node.type](node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
    else:
        tree = tokenize_expr(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
    
    return tree


def add_token_to_tree(node, tree, tk=None):
    if tk is None:
        tk = node.text.decode("utf-8")
    ln = get_linenos([node])
    tree.add(tk, ln)

def extend_tree_with_tks_lns(tks, lns, tree):
    for i in range(len(tks)):
        tree.add(tks[i], lns)

def combine_trees(tree, tree2):
    tks = tree2.tokens()
    lns = tree2.linenos()
    extend_tree_with_tks_lns(tks, lns, tree)
    for c in tree2.children():
        tree.add_child(c)
    if hasattr(tree, "else_clause") and hasattr(tree2, "else_clause") and not tree2.get_else() is None:
        tree.set_else(tree2.get_else())
    if hasattr(tree, "clauses") and hasattr(tree2, "clauses"):
        for c in tree2.get_clauses():
            tree.add_clause(c)
    if hasattr(tree, "set_name") and hasattr(tree2, "get_name") and not tree2.get_name() is None:
        tree.set_name(tree2.get_name())

def tree2ast(node, element,
             anonymize=True, anon_num=False, anon_params=False, anon_comments=True):
    names = {}
    imports = []
    import_from = {}
    tree = tokenize_node(node, names, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
    return tree
