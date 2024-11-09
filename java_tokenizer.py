#! /usr/bin/python3
# -*- coding: UTF-8 -*-

import json
from AST import Program, Class, Function, Instruction, Loop, If, Try, Switch, NodeWithElse

with open("./java_modules.json", "r") as f:
    modules = json.load(f)

builtins = [
    "wait",
    "equals",
    "toString",
    "hashCode",
    "getClass",
    "notify",
    "notifyAll",
    "clone",
    "length"
]

keywords = [
    "int",
    "char",
    "float",
    "boolean",
    "byte",
    "short",
    "long",
    "double",
    "new",
    "this"
]

def check_imports(module, tool="", modules=modules):
    module = module.replace("\n", "")
    tool = tool.replace("\n", "")
    current = modules
    path = module.split(".")
    for p in path:
        if not p in current:
            return None
        current = current[p]
    if len(tool) > 0:
        path = tool.split(".")
        for p in path:
            if not p in current:
                return None
            current = current[p]
    return current

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


def anonymize_id(node, names, params, funcs, classes, pattern, anon_num,
                 idtype="name"):
    tree = Instruction()
    name = node.text.decode("utf-8")
    target = pattern
    if anon_num:
        cpt = 1
        for e in names:
            if any([pattern in c for c in names[e]]):
                cpt += 1
        target += str(cpt)
    val = ["___"+target+"___"]
    if idtype == "name":
        names[name] = val
    elif idtype == "func":
        funcs[name] = val
    elif idtype == "class":
        classes[name] = val
    for tk in val:
        add_token_to_tree(node, tree, tk=tk)
    return tree

def anonymize_var(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    name = node.text.decode("utf-8")
    if anonymize:
        tr = anonymize_id(node, names, params, funcs, classes, "VAR", anon_num)
        combine_trees(tree, tr)
    else:
        tk = name
        add_token_to_tree(node, tree, tk=tk)
    return tree

def anonymize_param(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    name = node.text.decode("utf-8")
    if anonymize:
        if anon_params:
            pattern = "PARAM"
        else:
            pattern = "VAR"
        tr = anonymize_id(node, params, names, funcs, classes, pattern, anon_num)
        combine_trees(tree, tr)
    else:
        tk = name
        add_token_to_tree(node, tree, tk=tk)
    return tree

def anonymize_declared_name(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                            main=False, isclass=False, isconstructor=False):
    tree = Instruction()
    name = node.text.decode("utf-8")
    if anonymize:
        idtype = "class" if isclass else "func"
        if main:
            if isclass:
                pattern = "MAIN_CLASS"
            elif isconstructor:
                pattern = "CONSTRUCTOR"
            else:
                pattern = "MAIN_FUNCTION"
            tr = anonymize_id(node, names, params, funcs, classes, pattern, False,
                               idtype=idtype)
            combine_trees(tree, tr)
        elif name in funcs:
            for tk in funcs[name]:
                add_token_to_tree(node, tree, tk=tk)
        elif name in names and len(names[name]) == 1 and names[name][0] == "___TOOL___":
            for tk in names[name]:
                add_token_to_tree(node, tree, tk=tk)
        else:
            if isclass:
                pattern = "CLASS_NAME"
            elif isconstructor:
                pattern = "CONSTRUCTOR"
            else:
                pattern = "FUNCTION_NAME"
            tr = anonymize_id(node, names, params, funcs, classes, pattern, False,
                               idtype=idtype)
            combine_trees(tree, tr)
    else:
        add_token_to_tree(node, tree, tk=name)
    return tree

def anonymize_const(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    name = node.text.decode("utf-8")
    if anonymize:
        if node.type in ("decimal_integer_literal", "binary_integer_literal",
                         "octal_integer_literal", "hex_integer_literal"):
            if name[-1] in ("l", "L"):
                tk = "___CONST_LONG___"
            else:
                tk = "___CONST_INT___"
        elif node.type == "character_literal":
            tk = "___CONST_CHAR___"
        elif node.type == "string_literal":
            tk = "___CONST_STRING___"
        elif node.type in ("decimal_floating_point_literal", "hex_floating_point_literal"):
            if name[-1] in ("d", "D") or "e" in name or "E" in name:
                tk = "___CONST_DOUBLE___"
            else:
                tk = "___CONST_FLOAT___"
        elif node.type in ("true", "false"):
            tk = "___CONST_BOOL___"
        elif node.type == "null_literal":
            tk = "___CONST_NONE___"
        else:
            raise Exception("unknown constant: {} - {}".format(node.type, name))
    else:
        tk = name
    add_token_to_tree(node, tree, tk=tk)
    return tree

def anonymize_comment(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if anonymize and anon_comments:
        tk = "___COMMENT___"
    else:
        tk = node.text.decode("utf-8")
    comment = Instruction()
    add_token_to_tree(node, comment, tk=tk)
    tree.add_child(comment)
    return tree

def is_in_import_from(name, import_from):
    for module in import_from:
        if not check_imports(module, name) is None:
            return True
    return False

def is_in_imports(name, imports):
    for module in imports:
        if not check_imports(name, modules=imports[module]) is None:
            return True
    return False

def tokenize_identifier(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                        force_var=False, is_func_name=False, check_builtins=True, check_params=True):
    tree = Instruction()
    
    name = node.text.decode("utf-8")
    if force_var:
        if check_params and name in params and any(["PARAM" in c for c in params[name]]):
            for tk in params[name]:
                add_token_to_tree(node, tree, tk=tk)
        elif name in names and any(["VAR" in c for c in names[name]]):
            for tk in names[name]:
                add_token_to_tree(node, tree, tk=tk)
        else:
            tr = anonymize_var(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    elif is_func_name:
        if (is_in_import_from(name, import_from)) or (check_builtins and name in builtins) or (is_in_imports(name, imports)): # or is_fun(name):
            add_token_to_tree(node, tree, tk=name)
        else:
            if name in names and len(names[name]) == 1 and names[name][0] == "___TOOL___":
                for tk in names[name]:
                    add_token_to_tree(node, tree, tk=tk)
            else:
                funcs[name] = ["___FUNCTION_NAME___"]
                add_token_to_tree(node, tree, tk=funcs[name][0])
    elif check_params and name in params:
        for tk in params[name]:
            add_token_to_tree(node, tree, tk=tk)
    elif name in names:
        for tk in names[name]:
            add_token_to_tree(node, tree, tk=tk)
    elif (name in imports) or (is_in_import_from(name, import_from)) or (check_builtins and name in builtins) or (is_in_imports(name, imports)):
        add_token_to_tree(node, tree, tk=name)
    elif not check_imports("java.lang", name) is None:
        add_token_to_tree(node, tree, tk=name)
    else:
        tr = anonymize_var(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    
    return tree


def isinbuiltins(name, imports, import_from):
    if name in builtins:
        return True
    if name in keywords:
        return True
    if name in imports:
        return True
    if not check_imports(name, modules=modules["java"]["lang"]) is None:
        return True
    if is_in_imports(name, imports):
        return True
    if is_in_import_from(name, import_from):
        return True
    return False


def contains_identifier(node, imports, import_from):
    if node.type == "identifier":
        return not isinbuiltins(node.text.decode("utf-8"), imports, import_from)
    elif node.type in ("array_access", "field_access", "method_invocation"):
        return not isinbuiltins(node.children[0].text.decode("utf-8"), imports, import_from)
    else:
        for c in node.children:
            if contains_identifier(c, imports, import_from):
                return True
        return False


def tokenize_field_access(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    target = node.children[0]
    if target.type == "identifier":
        tr = tokenize_identifier(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type in ("this", "super"):
        add_token_to_tree(target, tree)
    elif target.type == "field_access":
        tr = tokenize_field_access(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "array_creation_expression":
        tr = tokenize_array_creation(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "method_invocation":
        tr = tokenize_call(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "parenthesized_expression":
        tr = tokenize_expr(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "array_access":
        tr = tokenize_array_access(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "object_creation_expression":
        tr = tokenize_object_creation_expression(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "class_literal":
        tr = tokenize_expr(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "string_literal":
        tr = anonymize_const(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        raise Exception("unknown field access target operand type: {}".format(target.type))
    
    for c in node.children[1:]:
        if c.type in (".", "this"):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                     check_params=False)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown field access operand type: {}".format(c.type))
    
    return tree


def tokenize_array_access(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    target = node.children[0]
    if target.type == "identifier":
        tr = tokenize_identifier(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "array_access":
        tr = tokenize_array_access(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "method_invocation":
        tr = tokenize_call(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "field_access":
        tr = tokenize_field_access(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "parenthesized_expression":
        tr = tokenize_expr(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif target.type == "array_creation_expression":
        tr = tokenize_array_creation(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        raise Exception("unknown array access target type: {}".format(target.type))
    
    if not any([contains_identifier(c, imports, import_from) for c in node.children[1:]]):
        tk = "___CONST_ACCESS___"
        add_token_to_tree(node, tree, tk=tk)
    else:
        for c in node.children[1:]:
            if c.type in ("[", "]"):
                add_token_to_tree(c, tree)
            elif c.type == "identifier":
                tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "array_access":
                tr = tokenize_array_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "decimal_integer_literal":
                tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            else:
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
    
    return tree


def tokenize_ternary_expression(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("?", ":"):
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree


def tokenize_array_creation(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if (node.children[-1].type == "array_initializer" and not contains_identifier(node.children[-1], imports, import_from)) or (node.children[-1].type == "dimensions_expr"):
        c = node.children[1]
        if c.type in ("integral_type", "floating_point_type", "boolean_type"):
            name = c.text.decode("utf-8")
        else:
            tr = tokenize_type_identifier(node.children[1], names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            if len(tr.tokens()) == 0:
                raise Exception("unknown array type format: {}".format(node.children[1].type))
            name = tr.tokens()[0]
        while name[0] == "_": name = name[1:]
        while name[-1] == "_": name = name[:-1]
        tk = "___CONST_ARRAY_{}___".format(name.upper())
        add_token_to_tree(node, tree, tk=tk)
    else:
        tr = tokenize_expr(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    return tree


def tokenize_cast_expression(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    for c in node.children:
        if c.type in ("(", ")"):
            add_token_to_tree(c, tree)
        elif c.type in ("integral_type", "floating_point_type", "boolean_type"):
            add_token_to_tree(c, tree)
        elif c.type in ("decimal_integer_literal", "character_literal", "string_literal",
                        "decimal_floating_point_literal", "octal_integer_literal", "hex_integer_literal",
                        "hex_floating_point_literal", "binary_integer_literal",
                        "true", "false", "null_literal"):
            tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "type_identifier":
            tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    
    return tree


def tokenize_assignment(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                        isparam=False):
    tree = Instruction()
    encountered_equal = False
    for c in node.children:
        if c.type == "identifier":
            if isparam:
                tr = anonymize_param(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            else:
                tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                          force_var=not encountered_equal)
            combine_trees(tree, tr)
        elif c.type in ("=", "+=", "-=", "/=", "*=", "%=", "^=", "&=", "|=",
                        ">>=", "<<=", "~=", ">>>=", "<<<="):
            encountered_equal = True
            add_token_to_tree(c, tree, tk=c.type)
        elif c.type == "this":
            add_token_to_tree(c, tree)
        elif c.type in ("decimal_integer_literal", "character_literal", "string_literal",
                        "decimal_floating_point_literal", "octal_integer_literal", "hex_integer_literal",
                        "hex_floating_point_literal", "binary_integer_literal",
                        "true", "false", "null_literal"):
            tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "class_literal":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_access":
            tr = tokenize_array_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "binary_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "ternary_expression":
            tr = tokenize_ternary_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "method_invocation":
            tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_creation_expression":
            tr = tokenize_array_creation(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "cast_expression":
            tr = tokenize_cast_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "object_creation_expression":
            tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "update_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "lambda_expression":
            tr = tokenize_lambda_expression(c, names.copy(), params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "field_access":
            tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "unary_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "parenthesized_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_initializer":
            tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "assignment_expression":
            tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "dimensions":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "instanceof_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "method_reference":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "switch_expression":
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                            force_extend_block=True)
            combine_trees(tree, tr)
        elif c.type == "underscore_pattern":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown assignment operand type: {}".format(c.type))
    return tree


def tokenize_lambda_expression(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in ("formal_parameters", "inferred_parameters"):
            for cc in c.children:
                if cc.type == "identifier":
                    tr = anonymize_param(cc, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                    combine_trees(tree, tr)
                elif cc.type in ("(", ")", ","):
                    add_token_to_tree(cc, tree)
                elif cc.type in ("formal_parameter", "spread_parameter"):
                    tr = tokenize_parameter(cc, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                    combine_trees(tree, tr)
                else:
                    raise Exception("unknown parameters operand type: {}".format(cc.type))
        elif c.type == "->":
            add_token_to_tree(c, tree, tk=c.type)
        elif c.type == "block":
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                               extend=True)
            combine_trees(tree, tr)
        elif c.type == "lambda_expression":
            tr = tokenize_lambda_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree


def tokenize_object_creation_expression(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    name = None
    if not contains_identifier(node, imports, import_from):
        if node.children[0].type == "new":
            i = 1
            while node.children[i].type in ("line_comment", "block_comment"):
                i += 1
            tr = tokenize_type_identifier(node.children[i], names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            if len(tr.tokens()) > 0:
                name = tr.tokens()[0]
        elif node.children[0].type == "{" and node.children[-1].type == "}":
            name = "ARRAY"
        elif node.children[1].type == "." and node.children[2].type == "new":
            i = 3
            while node.children[i].type in ("line_comment", "block_comment"):
                i += 1
            tr = tokenize_type_identifier(node.children[i], names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            if len(tr.tokens()) > 0:
                name = tr.tokens()[0]
        else:
            raise Exception("unknown object creation expression constant form: {}".format(node.text.decode("utf-8")))
        if not name is None:
            while name[0] == "_": name = name[1:]
            while name[-1] == "_": name = name[:-1]
            tk = "___CONST_{}___".format(name.upper())
            add_token_to_tree(node, tree, tk=tk)
    else:
        for c in node.children:
            if c.type in ("new", "this", ";", "{", "}", ",", ".",
                          "true", "false", "null"):
                add_token_to_tree(c, tree)
            elif c.type == "identifier":
                tr = anonymize_param(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "type_identifier":
                tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "argument_list":
                tr = tokenize_argument_list(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "generic_type":
                tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "class_body":
                tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "object_creation_expression":
                tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in ("string_literal", "character_literal", "null_literal",
                            "decimal_integer_literal", "decimal_floating_point_literal", "hex_integer_literal"):
                tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "scoped_type_identifier":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "annotation":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "method_invocation":
                tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "field_access":
                tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "binary_expression":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "array_creation_expression":
                tr = tokenize_array_creation(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in ("line_comment", "block_comment"):
                tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "marker_annotation":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "array_initializer":
                tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "ternary_expression":
                tr = tokenize_ternary_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "unary_expression":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "cast_expression":
                tr = tokenize_cast_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "parenthesized_expression":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "array_access":
                tr = tokenize_array_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "class_literal":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "lambda_expression":
                tr = tokenize_lambda_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "method_reference":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "type_arguments":
                tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            else:
                raise Exception("unknown object creation expression operand type: {}".format(c.type))
    return tree


def tokenize_type_identifier(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    name = None
    if node.type in ("type_identifier", "type_parameter", "scoped_type_identifier", "catch_type"):
        name = node.text.decode("utf-8")
    elif node.type in ("generic_type", "type_arguments", "array_type"):
        name = node.children[0].text.decode("utf-8")
    elif node.type == "annotated_type":
        for c in node.children:
            if "type" in c.type:
                tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                if len(tr.tokens()) > 0:#len(tks) > 0 and len(tks[0]) > 0:
                    name = tr.tokens()[0]
                    break
        if name is None:
            raise Exception("unknown annotated type operands: {}".format([c.type for c in node.children]))
    else:
        raise Exception("unknown type identifier type: {}".format(node.type))
    if isinbuiltins(name, imports, import_from):
        tk = name
        add_token_to_tree(node, tree, tk=tk)
    elif name in names:
        for tk in names[name]:
            add_token_to_tree(node, tree, tk=tk)
    else:
        tk = "___TYPE___"
        add_token_to_tree(node, tree, tk=tk)
    return tree


def tokenize_generic_type(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in ("<", ">", ",", "?", "super", "extends"):
            add_token_to_tree(c, tree)
        elif c.type in ("type_parameter", "type_identifier", "annotated_type"):
            tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "type_arguments":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "wildcard":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_type":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "scoped_type_identifier":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "generic_type":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "marker_annotation":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown generic type operand type: {}".format(c.type))
    return tree


def tokenize_variable_declaration(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in (";", ","):
            add_token_to_tree(c, tree)
        elif c.type in ("integral_type", "floating_point_type", "boolean_type"):
            add_token_to_tree(c, tree)
        elif c.type == "variable_declarator":
            tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_type":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "type_identifier":
            tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "generic_type":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "scoped_type_identifier":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "modifiers":
            tr = tokenize_modifiers(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown variable declaration operand type: {}".format(c.type))
    return tree


def tokenize_parameter(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            tr = anonymize_param(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("integral_type", "floating_point_type", "boolean_type",
                        "..."):
            add_token_to_tree(c, tree)
        elif c.type == "array_type":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "variable_declarator":
            tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                     isparam=True)
            combine_trees(tree, tr)
        elif c.type == "type_identifier":
            tk = c.text.decode("utf-8")
            if anonymize and not isinbuiltins(tk, imports, import_from):
                names[tk] = ["___TYPE___"]
                tk = names[tk][0]
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "generic_type":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "modifiers":
            tr = tokenize_modifiers(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "scoped_type_identifier":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "dimensions":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "underscore_pattern":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown parameter operand type: {}".format(c.type))
    return tree


def tokenize_argument_list(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    lastln = None
    for c in node.children:
        newln = get_linenos([c])
        if not lastln is None and lastln[-1] < newln[0]:
            add_token_to_tree(c, tree, tk="\n")
        
        if c.type in ("(", ")", ","):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "method_invocation":
            tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("decimal_integer_literal", "string_literal"):
            tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "field_access":
            tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("formal_parameter", "spread_parameter"):
            tr = tokenize_parameter(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "ternary_expression":
            tr = tokenize_ternary_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "object_creation_expression":
            tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "lambda_expression":
            tr = tokenize_lambda_expression(c, names.copy(), params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "assignment_expression":
            tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        lastln = newln
    return tree


def tokenize_call(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    
    target = node.children[0].text.decode("utf-8").replace("\n", "")
    if len(node.children) == 2 and (isinbuiltins(target, imports, import_from)):
        add_token_to_tree(node, tree, tk=target)
    elif len(node.children) > 2 and not (target in names and len(names[target]) == 1 and names[target][0] == "___TOOL___"):
        target += "." + node.children[2].text.decode("utf-8")
        i = 0
        while "." in target[i:] and i>=0:
            idx = target.find(".", i+1)
            if check_imports(target[:idx], modules=modules["java"]["lang"]) is None:
                break
            i = idx
        if i > 0:
            mods = target[:i].split(".")
            tools = target[i+1:].split(".")
            for mod in mods:
                add_token_to_tree(node, tree, tk=mod)
                add_token_to_tree(node, tree, tk=".")
            for i,tool in enumerate(tools):
                if i > 0:
                    add_token_to_tree(node, tree, tk=".")
                add_token_to_tree(node, tree, tk="___TOOL___")
    
    if node.children[-1].type == ";":
        iparams = -2
    else:
        iparams = -1
    
    if len(tree.tokens()) == 0:
        for i,c in enumerate(node.children[:iparams]):
            if c.type == "identifier":
                if i==len(node.children)-2:
                    tr = anonymize_declared_name(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                else:
                    tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in (".", "super", "this"):
                add_token_to_tree(c, tree)
            elif c.type == "field_access" and i==0:
                tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "array_creation_expression":
                tr = tokenize_array_creation(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "method_invocation":
                tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "class_literal":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in ("string_literal", "null_literal"):
                tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "parenthesized_expression":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "object_creation_expression":
                tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type in ("line_comment", "block_comment"):
                tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "type_arguments":
                tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            elif c.type == "array_access":
                tr = tokenize_array_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            else:
                raise Exception("unknown call operand type: {}".format(c.type))
    
    params_node = node.children[iparams]
    if params_node.type == "argument_list":
        tr = tokenize_argument_list(params_node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif params_node.type == "identifier":
        tr = tokenize_identifier(params_node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                 is_func_name=True)
        combine_trees(tree, tr)
    elif params_node.type == "this":
        add_token_to_tree(params_node, tree)
    else:
        raise Exception("unknown call params type: {}".format(params_node.type))
    
    if iparams < -1:
        last = node.children[-1]
        if last.type == ";":
            add_token_to_tree(last, tree)
        else:
            raise Exception("unknown call operand type after params: {}".format(last.type))
    
    return tree


def tokenize_labeled_expr(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            name = c.text.decode("utf-8")
            names[name] = ["___LABEL___"]
            tk = names[name][0]
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == ":":
            add_token_to_tree(c, tree)
            if not c.next_sibling is None:
                cln = get_linenos([c])
                nextln = get_linenos([c.next_sibling])
                if cln != nextln:
                    add_token_to_tree(c, tree, tk="\n")
        elif c.type == ";":
            add_token_to_tree(c, tree)
        elif c.type in ("if_statement", "while_statement", "do_statement", "switch_expression", "try_statement"):
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "expression_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "enhanced_for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "block":
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "labeled_statement":
            tr = tokenize_labeled_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("break_statement", "return_statement"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "synchronized_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown labeled expression operand type: {}".format(c.type))
    return tree


def tokenize_expr(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    if len(node.children) == 0 or node.type in ("string_literal",):
        if node.type in (".", "(", ")", "[", "]", "{", "}", "=", ",", ";", ":",
                         "&&", "||", "!", "<", ">", "<=", ">=", "==", "!=",
                         "+", "-", "*", "/", "%", "&", "|", "~", "^", "++", "--",
                         "<<", ">>", "<<<", ">>>", "?", "::", "@"):
            tk = node.type
            add_token_to_tree(node, tree, tk=tk)
        elif node.type in keywords or node.type in ("boolean_type", "void_type", "extends", "implements",
                                                    "return", "false", "true", "class",
                                                    "module", "requires", "exports", "provides", "with", "to", "uses", "transitive", "opens", "open",
                                                    "instanceof", "synchronized", "break", "continue", "static",
                                                    "super", "assert", "yield", "throws", "underscore_pattern"):
            add_token_to_tree(node, tree)
        elif node.type == "identifier":
            tr = tokenize_identifier(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif node.type in ("decimal_integer_literal", "character_literal", "string_literal", "decimal_floating_point_literal",
                           "hex_integer_literal", "octal_integer_literal", "hex_floating_point_literal", "binary_integer_literal",
                           "null_literal"):
            tr = anonymize_const(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif node.type == "type_identifier":
            tr = tokenize_type_identifier(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif node.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown expression operand type: {}".format(node.type))
    elif node.type == "object_creation_expression":
        tr = tokenize_object_creation_expression(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "lambda_expression":
        tr = tokenize_lambda_expression(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "modifiers":
        tr = tokenize_modifiers(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "assignment_expression":
        tr = tokenize_assignment(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    elif node.type == "switch_expression":
        tr = tokenize_blocked_statement(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        for c in node.children:
            if c.type == "assignment_expression":
                tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "binary_expression":
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "method_invocation":
                tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "string_literal":
                tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "ternary_expression":
                tr = tokenize_ternary_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "block":
                tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "object_creation_expression":
                tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "lambda_expression":
                tr = tokenize_lambda_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            elif c.type == "module_body":
                tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            else:
                tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree


def tokenize_blocked_statement(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                               force_extend_block=False):
    if node.type == "if_statement":
        tree = If()
    elif node.type in ("try_statement", "try_with_resources_statement"):
        tree = Try()
    elif node.type == "switch_expression":
        tree = Switch()
    elif node.type in ("while_statement", "do_statement"):
        tree = Loop()
        if node.type == "do_statement":
            tree.enable_do_else_at_each_iteration()
    else:
        tree = Instruction()
    else_clause = None
    clauses = []
    current = tree
    lastc = None
    for i,c in enumerate(node.children):
        tr = None
        if c.type in ("if", "else", "while", "try", "catch", "switch", "finally", "do"):
            if c.type == "else" or (c.type == "while" and node.type == "do_statement"):
                current = Instruction()
                else_clause = current
            add_token_to_tree(c, current)
        elif c.type in ("(", ")", ";"):
            add_token_to_tree(c, current)
        elif c.type == "condition":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(current, tr)
            tr = None
        elif c.type == "catch_clause":
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            clauses.append(tr)
            tr = None
        elif c.type == "finally_clause":
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            else_clause = tr
            tr = None
        elif c.type in ("if_statement", "finally_clause", "try_statement", "while_statement", "switch_expression", "do_statement", "try_with_resources_statement"):
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            if c.type in ("while_statement", "do_statement") and current.type != "Loop":
                tmp = Loop()
                if else_clause == current:
                    else_clause = tmp
                elif current in clauses:
                    j = clauses.index(current)
                    clauses[j] = tmp
                elif current == tree:
                    tree = tmp
                combine_trees(tmp, current)
                current = tmp
        elif c.type in ("expression_statement", "binary_expression", "update_expression", "resource_specification"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "local_variable_declaration":
            tr = tokenize_variable_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("block", "switch_block"):
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                               extend=force_extend_block)
            if node.type == "switch_expression":
                if not force_extend_block:
                    children = tr.children()
                    if children[0].tokens() == ["{"]:
                        current.prefix = children.pop(0)
                    if children[-1].tokens() == ["}"]:
                        current.suffix = children.pop(-1)
                    clauses.extend(children)
                else:
                    combine_trees(current, tr)
                if hasattr(tr, "get_else") and not tr.get_else() is None:
                    else_clause = tr.get_else()
            else:
                combine_trees(current, tr)
            tr = None
        elif c.type == "parenthesized_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "return_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "throw_statement":
            tr = tokenize_throw_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("continue_statement", "break_statement"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "assert_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "synchronized_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "enhanced_for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "catch_formal_parameter":
            tr = tokenize_catch_parameter(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "labeled_statement":
            tr = tokenize_labeled_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        else:
            raise Exception("unknown blocked statement operand type: {}".format(c.type))
        if not tr is None:
            if lastc in ("condition", "else"):
                current.add_child(tr)
            else:
                combine_trees(current, tr)
        lastc = c.type
    if not else_clause is None:
        tree.set_else(else_clause)
    if len(clauses) > 0:
        for e in clauses:
            tree.add_clause(e)
    return tree


def tokenize_catch_parameter(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                      force_var=True)
            combine_trees(tree, tr)
        elif c.type == "catch_type":
            tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "modifiers":
            tr = tokenize_modifiers(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "underscore_pattern":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown catch parameter operand type: {}".format(c.type))
    return tree


def tokenize_for_statement(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Loop()
    for i, c in enumerate(node.children):
        tr = None
        if c.type == "identifier":
            tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("for", "(", ")", ":", "this", ";", "true", "false", ",",
                        "integral_type", "boolean_type", "floating_point_type"):
            add_token_to_tree(c, tree)
        elif c.type == "block":
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "type_identifier":
            tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "method_invocation":
            tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "field_access":
            tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "generic_type":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "scoped_type_identifier":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "modifiers":
            tr = tokenize_modifiers(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "expression_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "cast_expression":
            tr = tokenize_cast_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "array_type":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "local_variable_declaration":
            tr = tokenize_variable_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "array_access":
            tr = tokenize_array_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "object_creation_expression":
            tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "binary_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "instanceof_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "unary_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "update_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("if_statement", "try_statement", "while_statement", "switch_expression", "do_statement"):
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "parenthesized_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "ternary_expression":
            tr = tokenize_ternary_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "array_creation_expression":
            tr = tokenize_array_creation(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "assignment_expression":
            tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "assert_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "enhanced_for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "dimensions":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("continue_statement", "break_statement"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "return_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "synchronized_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "null_literal":
            tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        else:
            raise Exception("unknown enhanced for statement operand type: {}".format(c.type))
        if not tr is None:
            if i < len(node.children)-1 or c.type == "block":
                combine_trees(tree, tr)
            else:
                tree.add_child(tr)
    return tree


def tokenize_modifiers(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    lastln = None
    for c in node.children:
        currentln = get_linenos([c])
        if not lastln is None and currentln != lastln:
            add_token_to_tree(c, tree, tk="\n")
        
        if c.type in ("marker_annotation", "annotation"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("public", "private", "protected",
                        "static", "final", "abstract",
                        "volatile", "native", "synchronized", "transient",
                        "default", "strictfp"):
            tk = c.text.decode("utf-8")
            add_token_to_tree(c, tree, tk=tk)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown modifiers operand type: {}".format(c.type))
        lastln = currentln
    return tree


def tokenize_declaration(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    anonymizer_params = {}
    if node.type in ("class_declaration", "interface_declaration", "annotation_type_declaration", "enum_declaration"):
        anonymizer_params["isclass"] = True
        anonymizer_params["main"] = True
        tree = Class()
    elif node.type == "method_declaration":
        anonymizer_params["main"] = True
        tree = Function()
    elif node.type == "constructor_declaration":
        anonymizer_params["isconstructor"] = True
        tree = Function()
    elif node.type in ("field_declaration", "constant_declaration", "annotation_type_element_declaration", "module_declaration"):
        tree = Instruction()
    else:
        raise Exception("unknown declaration type: {}".format(node.type))
    for c in node.children:
        if c.type == "modifiers":
            tr = tokenize_modifiers(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("void_type", "class", "interface", "@interface", "enum",
                        ";", "(", ")", ",", "default",
                        "boolean_type", "integral_type", "floating_point_type",
                        "true", "false"):
            tk = c.text.decode("utf-8")
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "generic_type":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "identifier":
            tr = anonymize_declared_name(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                                          **anonymizer_params)
            if node.type == "method_declaration":
                name = c.text.decode("utf-8")
                tree.set_name(name)
            elif node.type == "constructor_declaration":
                tree.set_name("___CONSTRUCTOR___")
            combine_trees(tree, tr)
            names = names.copy()
            params = params.copy()
        elif c.type == "formal_parameters":
            tr = tokenize_argument_list(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("block", "class_body", "interface_body", "constructor_body", "annotation_type_body", "enum_body"):
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            # tree.add_child(tr)
            combine_trees(tree, tr)
        elif c.type in ("superclass", "super_interfaces"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "type_identifier":
            tr = tokenize_type_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "variable_declarator":
            tr = tokenize_assignment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "type_parameters":
            tr = tokenize_generic_type(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_type":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "extends_interfaces":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "element_value_array_initializer":
            tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "string_literal":
            tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "field_access":
            tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "scoped_type_identifier":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "throws":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree


def tokenize_scoped_identifier(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    target = node.children[0]
    if target.type == "identifier":
        tk = target.text.decode("utf-8")
        if anonymize and not tk in modules:
            tk = "___MODULE___"
        add_token_to_tree(target, tree, tk=tk)
    elif target.type == "scoped_identifier":
        tr = tokenize_scoped_identifier(target, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        combine_trees(tree, tr)
    else:
        raise Exception("unknown scoped identifier operand type: {}".format(target.type))
    add_token_to_tree(node.children[1], tree)
    tk = node.children[2].text.decode("utf-8")
    module = target.text.decode("utf-8")
    if check_imports(module, tool=tk) is None:
        tk = "___TOOL___"
    add_token_to_tree(node.children[2], tree, tk=tk)
    return tree


def tokenize_import_declaration(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    imported = None
    asterisk = False
    for c in node.children:
        if c.type in ("import", ";", ".", "static"):
            add_token_to_tree(c, tree)
        elif c.type == "scoped_identifier":
            imported = c
            tr = tokenize_scoped_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "asterisk":
            asterisk = True
            tk = c.children[0].text.decode("utf-8")
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "identifier":
            imported = c
            tk = "___MODULE___"
            add_token_to_tree(c, tree, tk=tk)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown import declaration operand type: {}".format(c.type))
    if asterisk:
        import_from.append(imported.text.decode("utf-8"))
    elif len(imported.children) > 0:
        tool = imported.children[-1].text.decode("utf-8")
        content = check_imports(imported.children[0].text.decode("utf-8"), tool=tool)
        if not content is None:
            imports[tool] = content
        else:
            names[tool] = ["___TOOL___"]
    return tree


def tokenize_enum_constant(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    iid = 0
    for c in node.children:
        if c.type == "identifier":
            if iid == 0:
                tk = "___TOOL___"
                add_token_to_tree(c, tree, tk=tk)
            else:
                tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
                combine_trees(tree, tr)
            iid += 1
        elif c.type == "argument_list":
            tr = tokenize_argument_list(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "class_body":
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            tree.add_child(tr)
        elif c.type == "modifiers":
            tr = tokenize_modifiers(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("line_comment", "block_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown enum constant operand type: {}".format(c.type))
    return tree


def tokenize_tree(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                  extend=False):
    if node.type == "program":
        tree = Program()
    else:
        tree = Instruction()
    lastln = None
    tks = []
    for c in node.children:
        tr = None
        ln = get_linenos([c])
        if c.type in (":", ";", ","):
            if node.type == "switch_block_statement_group" and c.type == ":":
                add_token_to_tree(c, tree)
            elif node.type == "switch_block_statement_group" and c.type == ";":
                tr = Instruction()
                add_token_to_tree(c, tr)
            else:
                tks.append(c)
        elif c.type in ("{", "}"):
            tr = Instruction()
            add_token_to_tree(c, tr)
        elif c.type == "local_variable_declaration":
            tr = tokenize_variable_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("block_comment", "line_comment"):
            tr = anonymize_comment(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("if_statement", "while_statement", "try_statement", "switch_expression", "do_statement", "try_with_resources_statement"):
            tr = tokenize_blocked_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "enhanced_for_statement":
            tr = tokenize_for_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("expression_statement", "return_statement", "break_statement", "continue_statement"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("method_declaration", "constructor_declaration", "field_declaration", "annotation_type_element_declaration"):
            tr = tokenize_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "import_declaration":
            tr = tokenize_import_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("class_declaration", "interface_declaration", "annotation_type_declaration", "enum_declaration", "module_declaration"):
            tr = tokenize_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "package_declaration":
            tr = tokenize_package_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "explicit_constructor_invocation":
            tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "throw_statement":
            tr = tokenize_throw_statement(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "constant_declaration":
            tr = tokenize_declaration(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("block", "switch_block_statement_group"):
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments,
                               extend=extend or c.type=="block")
            if tr.tokens()[0] == "default" and not extend:
                if tree.type == "Instruction":
                    tmp = NodeWithElse()
                    combine_trees(tmp, tree)
                    tree = tmp
                tree.set_else(tr)
                tr = None
        elif c.type == "switch_label":
            tr = tokenize_switch_label(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
            tr = None
        elif c.type == "enum_constant":
            tr = tokenize_enum_constant(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "synchronized_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "static_initializer":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "labeled_statement":
            tr = tokenize_labeled_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "enum_body_declarations":
            tr = tokenize_tree(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "assert_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type == "yield_statement":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        elif c.type in ("requires_module_directive", "exports_module_directive", "provides_module_directive"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
        else:
            raise Exception("unknown expression type: {}".format(c.type))
        if not tr is None:
            if len(tks) > 0:
                before = Instruction()
                lastcln = None
                if len(tree.linenos()) > 0:
                    lastcln = tree.linenos()
                for c in tks:
                    cln = get_linenos([c])
                    if not lastcln is None and cln[0] > lastcln[-1] and len(before.tokens()) > 0 and before.tokens()[-1] != "\n":
                        add_token_to_tree(c, before, tk="\n")
                    add_token_to_tree(c, before)
                    lastcln = cln
                if extend:
                    combine_trees(tree, before)
                else:
                    # if not node.parent is None: print(node.parent.type, node.type)
                    tree.add_child(before)
                tks = []
            if extend:
                if not lastln is None and ln[0] > lastln[-1]:
                    add_token_to_tree(c, tree, tk="\n")
                combine_trees(tree, tr)
            else:
                # if not node.parent is None: print(node.parent.type, node.type)
                tree.add_child(tr)
        lastln = ln
    if len(tks) > 0:
        if len(tree.children()) > 0:
            after = Instruction()
            lastcln = None
            if len(tree.linenos()) > 0:
                lastcln = tree.linenos()
            for c in tks:
                cln = get_linenos([c])
                if not lastcln is None and cln[0] > lastcln[-1] and len(after.tokens()) > 0 and after.tokens()[-1] != "\n":
                    add_token_to_tree(c, after, tk="\n")
                add_token_to_tree(c, after)
                lastcln = cln
            if extend:
                combine_trees(tree, after)
            else:
                # if not node.parent is None: print(node.parent.type, node.type)
                tree.add_child(after)
        else:
            lastcln = None
            if len(tree.linenos()) > 0:
                lastcln = tree.linenos()
            for c in tks:
                cln = get_linenos([c])
                if not lastcln is None and cln[0] > lastcln[-1] and len(tree.tokens()) > 0 and tree.tokens()[-1] != "\n":
                    add_token_to_tree(c, tree, tk="\n")
                add_token_to_tree(c, tree)
                lastcln = cln
    return tree


def tokenize_switch_label(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in ("case", "default"):
            add_token_to_tree(c, tree)
        else:
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
    return tree


def tokenize_throw_statement(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in ("throw", ";", "this"):
            add_token_to_tree(c, tree)
        elif c.type == "identifier":
            tr = tokenize_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "null_literal":
            tr = anonymize_const(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "object_creation_expression":
            tr = tokenize_object_creation_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "method_invocation":
            tr = tokenize_call(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "field_access":
            tr = tokenize_field_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "cast_expression":
            tr = tokenize_cast_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "parenthesized_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "ternary_expression":
            tr = tokenize_ternary_expression(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_access":
            tr = tokenize_array_access(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "binary_expression":
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type == "array_creation_expression":
            tr = tokenize_array_creation(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown throw statement operand type: {}".format(c.type))
    return tree


def tokenize_package_declaration(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments):
    tree = Instruction()
    for c in node.children:
        if c.type in ("package", ";"):
            add_token_to_tree(c, tree)
        elif c.type in "identifier":
            tk = c.text.decode("utf-8")
            if anonymize and not tk in modules:
                names[tk] = ["___MODULE___"]
                tk = names[tk][0]
            add_token_to_tree(c, tree, tk=tk)
        elif c.type == "scoped_identifier":
            tr = tokenize_scoped_identifier(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        elif c.type in ("marker_annotation", "annotation"):
            tr = tokenize_expr(c, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
            combine_trees(tree, tr)
        else:
            raise Exception("unknown package declaration operand type: {}".format(c.type))
    return tree


def add_token_to_tree(node, tree, tk=None):
    if tk is None:
        tk = node.text.decode("utf-8")
    if len(tk) > 0:
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
        if tree2.do_else_anyway():
            tree.enable_do_else_anyway()
    if hasattr(tree, "clauses") and hasattr(tree2, "clauses"):
        for c in tree2.get_clauses():
            tree.add_clause(c)

def tree2ast(node, element,
             anonymize=True, anon_num=False, anon_params=False, anon_comments=True):
    names = {}
    params = {}
    funcs = {}
    classes = {}
    imports = {}
    import_from = []
    tree = tokenize_tree(node, names, params, funcs, classes, imports, import_from, anonymize, anon_num, anon_params, anon_comments)
    return tree
