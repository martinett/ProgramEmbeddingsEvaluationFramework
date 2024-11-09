#! /usr/bin/python3
# -*- coding: UTF-8 -*-

programs = {
    "python": {
        "sum_list": {
            "for_e": """
def sum_list(l):
    res = 0
    for elem in l:
        res += elem
    return res
""",
            "for_i": """
def sum_list(l):
    res = 0
    for i in range(len(l)):
        res += l[i]
    return res
""",
            "while": """
def sum_list(l):
    res = 0
    i = 0
    while i < len(l):
        res += l[i]
        i += 1
    return res
""",
            "recursive": """
def sum_list(l):
    if len(l) == 0:
        return 0
    return l[0]+sum_list(l[1:])
"""
        },
        "sum_even_list": {
            "for_e": """
def sum_even_list(l):
    res = 0
    for elem in l:
        if elem%2 == 0:
            res += elem
    return res
""",
            "for_i": """
def sum_even_list(l):
    res = 0
    for i in range(len(l)):
        if l[i]%2 == 0:
            res += l[i]
    return res
""",
            "while": """
def sum_even_list(l):
    res = 0
    i = 0
    while i < len(l):
        if l[i]%2 == 0:
            res += l[i]
        i += 1
    return res
""",
            "recursive": """
def sum_even_list(l):
    if len(l) == 0:
        return 0
    if l[0]%2 == 0:
        return l[0]+sum_even_list(l[1:])
    return sum_even_list(l[1:])
"""
        },
        "sum_odd_list": {
            "for_e": """
def sum_odd_list(l):
    res = 0
    for elem in l:
        if elem%2 != 0:
            res += elem
    return res
""",
            "for_i": """
def sum_odd_list(l):
    res = 0
    for i in range(len(l)):
        if l[i]%2 != 0:
            res += l[i]
    return res
""",
            "while": """
def sum_odd_list(l):
    res = 0
    i = 0
    while i < len(l):
        if l[i]%2 != 0:
            res += l[i]
        i += 1
    return res
""",
            "recursive": """
def sum_odd_list(l):
    if len(l) == 0:
        return 0
    if l[0]%2 != 0:
        return l[0]+sum_odd_list(l[1:])
    return sum_odd_list(l[1:])
"""
        },
        "mean_list": {
            "for_e": """
def mean_list(l):
    if len(l) == 0:
        return None
    res = 0
    for elem in l:
        res += elem
    return res/len(l)
""",
            "for_i": """
def mean_list(l):
    if len(l) == 0:
        return None
    res = 0
    for i in range(len(l)):
        res += l[i]
    return res/len(l)
""",
            "while": """
def mean_list(l):
    if len(l) == 0:
        return None
    res = 0
    i = 0
    while i < len(l):
        res += l[i]
        i += 1
    return res/len(l)
"""
        },
        "min_list": {
            "for_e": """
def min_list(l):
    if len(l) == 0:
        return None
    min = None
    for elem in l:
        if min == None or elem < min:
            min = elem
    return min
""",
            "for_i": """
def min_list(l):
    if len(l) == 0:
        return None
    min = l[0]
    for i in range(1, len(l)):
        if l[i] < min:
            min = l[i]
    return min
""",
            "while": """
def min_list(l):
    if len(l) == 0:
        return None
    min = l[0]
    i = 0
    while i < len(l):
        if l[i] < min:
            min = l[i]
        i += 1
    return min
"""
        },
        "max_list": {
            "for_e": """
def max_list(l):
    if len(l) == 0:
        return None
    max = None
    for elem in l:
        if max == None or elem > max:
            max = elem
    return max
""",
            "for_i": """
def max_list(l):
    if len(l) == 0:
        return None
    max = l[0]
    for i in range(1, len(l)):
        if l[i] > max:
            max = l[i]
    return max
""",
            "while": """
def max_list(l):
    if len(l) == 0:
        return None
    max = l[0]
    i = 1
    while i < len(l):
        if l[i] > max:
            max = l[i]
        i += 1
    return max
"""
        },
        "is_ascending_list": {
            "for_e": """
def is_ascending_list(l):
    prev = None
    for elem in l:
        if prev != None and prev > elem:
            return False
        prev = elem
    return True
""",
            "for_i": """
def is_ascending_list(l):
    for i in range(1, len(l)):
        if l[i-1] > l[i]:
            return False
    return True
""",
            "while": """
def is_ascending_list(l):
    i = 1
    while i < len(l):
        if l[i-1] > l[i]:
            return False
        i += 1
    return True
""",
            "recursive": """
def is_ascending_list(l):
    if len(l) < 2:
        return True
    if l[0] > l[1]:
        return False
    return is_ascending_list(l[1:])
"""
        },
        "is_descending_list": {
            "for_e": """
def is_descending_list(l):
    prev = None
    for elem in l:
        if prev != None and prev < elem:
            return False
        prev = elem
    return True
""",
            "for_i": """
def is_descending_list(l):
    for i in range(1, len(l)):
        if l[i-1] < l[i]:
            return False
    return True
""",
            "while": """
def is_descending_list(l):
    i = 1
    while i < len(l):
        if l[i-1] < l[i]:
            return False
        i += 1
    return True
""",
            "recursive": """
def is_descending_list(l):
    if len(l) < 2:
        return True
    if l[0] < l[1]:
        return False
    return is_descending_list(l[1:])
"""
        },
        "display_list": {
            "for_e": """
def display_list(l):
    for elem in l:
        print(elem)
""",
            "for_i": """
def display_list(l):
    for i in range(len(l)):
        print(l[i])
""",
            "while": """
def display_list(l):
    i = 0
    while i < len(l):
        print(l[i])
        i += 1
""",
            "recursive": """
def display_list(l):
    if len(l) > 0:
        print(l[0])
        display_list(l[1:])
"""
        },
        "factorial": {
            "for_i": """
def factorial(n):
    res = 1
    for i in range(2, n+1):
        res *= i
    return res
""",
            "while": """
def factorial(n):
    res = 1
    i = 2
    while i <= n:
        res *= i
        i += 1
    return res
""",
            "recursive": """
def factorial(n):
    if n < 1 :
        return 1
    return n * factorial(n-1)
"""
        },
        "op_on_element": {
            "op+": """
def add(x): 
    return x + 1
""",
            "op*": """
def mult(x):
    return x * 2
""",
            "op<": """
def lower(x):
    return x < 0
""",
            "op<=": """
def leq(x):
    return x <= 0
""",
            "op>": """
def greater(x):
    return x > 0
""",
            "op>=": """
def geq(x):
    return x >= 0
""",
            "op==": """
def eq(x):
    return x == 0
""",
            "op!=": """
def neq(x):
    return x != 0
"""
        },
        "op_on_elements": {
            "op+": """
def add(a, b):
    return a + b
""",
            "op*": """
def mult(a, b):
    return a * b
""",
            "op<": """
def lower(a, b):
    return a < b
""",
            "op<=": """
def leq(a, b):
    return a <= b
""",
            "op>": """
def greater(a, b):
    return a > b
""",
            "op>=": """
def geq(a, b):
    return a >= b
""",
            "op==": """
def eq(a, b):
    return a == b
""",
            "op!=": """
def neq(a, b):
    return a != b
"""
        },
        "map": {
            "op+": """
def add(l):
    return [e + 1 for e in l]
""",
            "op*": """
def mult(l):
    return [e * 2 for e in l]
""",
            "op<": """
def lower(l):
    return [e < 0 for e in l]
""",
            "op<=": """
def leq(l):
    return [e <= 0 for e in l]
""",
            "op>": """
def greater(l):
    return [e > 0 for e in l]
""",
            "op>=": """
def geq(l):
    return [e >= 0 for e in l]
""",
            "op==": """
def eq(l):
    return [e == 0 for e in l]
""",
            "op!=": """
def neq(l):
    return [e != 0 for e in l]
"""
        },
        "reduce": {
            "op+": """
def add(l):
    res = 0
    for e in l:
        res += e
    return res
""",
            "op*": """
def mult(l):
    res = 1
    for e in l:
        res *= e
    return res
"""
        }
    },
    "java": {
        "sum_list": {
            "for_e": """
import java.util.List;
public int sum_list(List<Integer> l) {
    int res = 0;
    for (int elem : l) {
        res += elem;
    }
    return res;
}
""",
            "for_i": """
import java.util.List;
public int sum_list(List<Integer> l) {
    int res = 0;
    for (int i = 0; i < l.size(); i++) {
        res += l.get(i);
    }
    return res;
}
""",
            "while": """
import java.util.List;
public int sum_list(List<Integer> l) {
    int res = 0;
    int i = 0;
    while (i < l.size()) {
        res += l.get(i);
        i++;
    }
    return res;
}
""",
            "recursive": """
import java.util.List;
public int sum_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    return l.get(0) + sum_list(l.subList(1, l.size()));
}
"""
        },
        "sum_even_list": {
            "for_e": """
import java.util.List;
public int sum_even_list(List<Integer> l) {
    int res = 0;
    for (int elem : l) {
        if (elem%2 == 0) {
            res += elem;
        }
    }
    return res;
}
""",
            "for_i": """
import java.util.List;
public int sum_even_list(List<Integer> l) {
    int res = 0;
    for (int i = 0; i < l.size(); i++) {
        if (l.get(i)%2 == 0) {
            res += l.get(i);
        }
    }
    return res;
}
""",
            "while": """
import java.util.List;
public int sum_even_list(List<Integer> l) {
    int res = 0;
    int i = 0;
    while (i < l.size()) {
        if (l.get(i)%2 == 0) {
            res += l.get(i);
        }
        i++;
    }
    return res;
}
""",
            "recursive": """
import java.util.List;
public int sum_even_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    if (l.get(0)%2 == 0) {
        return l[0]+sum_even_list(l.subList(1, l.size()));
    }
    return sum_even_list(l.subList(1, l.size()));
}
"""
        },
        "sum_odd_list": {
            "for_e": """
import java.util.List;
public int sum_odd_list(List<Integer> l) {
    int res = 0;
    for (int elem : l) {
        if (elem%2 != 0) {
            res += elem;
        }
    }
    return res;
}
""",
            "for_i": """
import java.util.List;
public int sum_odd_list(List<Integer> l) {
    int res = 0;
    for (int i = 0; i < l.size(); i++) {
        if (l.get(i)%2 != 0) {
            res += l.get(i);
        }
    }
    return res;
}
""",
            "while": """
import java.util.List;
public int sum_odd_list(List<Integer> l) {
    int res = 0;
    int i = 0;
    while (i < l.size()) {
        if (l.get(i)%2 != 0) {
            res += l.get(i);
        }
        i++;
    }
    return res;
}
""",
            "recursive": """
import java.util.List;
public int sum_odd_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    if (l.get(0)%2 != 0) {
        return l.get(0) + sum_odd_list(l.subList(1, l.size()));
    }
    return sum_odd_list(l.subList(1, l.size()));
}
"""
        },
        "mean_list": {
            "for_e": """
import java.util.List;
public float mean_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    float res = 0;
    for (int elem : l) {
        res += elem;
    }
    return res/l.size();
}
""",
            "for_i": """
import java.util.List;
public float mean_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    float res = 0;
    for (int i = 0; i < l.size(); i++) {
        res += l.get(i);
    }
    return res/l.size();
}
""",
            "while": """
import java.util.List;
public float mean_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    float res = 0;
    int i = 0;
    while (i < l.size()) {
        res += l.get(i);
        i++;
    }
    return res/l.size();
}
"""
        },
        "min_list": {
            "for_e": """
import java.util.List;
public int min_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    int min = Integer.MAX_VALUE;
    for (int elem : l) {
        if (elem < min) {
            min = elem;
        }
    }
    return min;
}
""",
            "for_i": """
import java.util.List;
public int min_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    int min = l.get(0);
    for (int i = 1; i < l.size(); i++) {
        if (l.get(i) < min) {
            min = l.get(i);
        }
    }
    return min;
}
""",
            "while": """
import java.util.List;
public int min_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    int min = l.get(0);
    int i = 0;
    while (i < l.size()) {
        if (l.get(i) < min) {
            min = l.get(i);
        }
        i++;
    }
    return min;
}
"""
        },
        "max_list": {
            "for_e": """
import java.util.List;
public int max_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    int max = Integer.MIN_VALUE;
    for (int elem : l) {
        if (elem > max) {
            max = elem;
        }
    }
    return max;
}
""",
            "for_i": """
import java.util.List;
public int max_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    int max = l.get(0);
    for (int i = 1; i < l.size(); i++) {
        if (l.get(i) > max) {
            max = l.get(i);
        }
    }
    return max;
}
""",
            "while": """
import java.util.List;
public int max_list(List<Integer> l) {
    if (l.size() == 0) {
        return 0;
    }
    int max = l.get(0);
    int i = 1;
    while (i < l.size()) {
        if (l.get(i) > max) {
            max = l.get(i);
        }
        i++;
    }
    return max;
}
"""
        },
        "is_ascending_list": {
            "for_e": """
import java.util.List;
public boolean is_ascending_list(List<Integer> l) {
    int prev = Integer.MIN_VALUE;
    for (int elem : l) {
        if (prev > elem) {
            return false;
        }
    }
    return true;
}
""",
            "for_i": """
import java.util.List;
public boolean is_ascending_list(List<Integer> l) {
    for (int i = 1; i < l.size(); i++) {
        if (l.get(i-1) > l.get(i)) {
            return false;
        }
    }
    return true;
}
""",
            "while": """
import java.util.List;
public boolean is_ascending_list(List<Integer> l) {
    int i = 1;
    while (i < l.size()) {
        if (l.get(i-1) > l.get(i)) {
            return false;
        }
        i++;
    }
    return true;
}
""",
            "recursive": """
import java.util.List;
public boolean is_ascending_list(List<Integer> l) {
    if (l.size() < 2) {
        return true;
    }
    if (l.get(0) > l.get(1)) {
        return false;
    }
    return is_ascending_list(l.subList(1, l.size()));
}
"""
        },
        "is_descending_list": {
            "for_e": """
import java.util.List;
public boolean is_descending_list(List<Integer> l) {
    int prev = Integer.MAX_VALUE;
    for (int elem : l) {
        if (prev < elem) {
            return false;
        }
    }
    return true;
}
""",
            "for_i": """
import java.util.List;
public boolean is_descending_list(List<Integer> l) {
    for (int i = 1; i < l.size(); i++) {
        if (l.get(i-1) < l.get(i)) {
            return false;
        }
    }
    return true;
}
""",
            "while": """
import java.util.List;
public boolean is_descending_list(List<Integer> l) {
    int i = 1;
    while (i < l.size()) {
        if (l.get(i-1) < l.get(i)) {
            return false;
        }
        i++;
    }
    return true;
}
""",
            "recursive": """
import java.util.List;
public boolean is_descending_list(List<Integer> l) {
    if (l.size() < 2) {
        return true;
    }
    if (l.get(0) < l.get(1)) {
        return false;
    }
    return is_descending_list(l.subList(1, l.size()));
}
"""
        },
        "display_list": {
            "for_e": """
import java.util.List;
public void display_list(List<Integer> l) {
    for (int elem : l) {
        System.out.println(elem);
    }
}
""",
            "for_i": """
import java.util.List;
public void display_list(List<Integer> l) {
    for (int i = 0; i < l.size(); i++) {
        System.out.println(l.get(i));
    }
}
""",
            "while": """
import java.util.List;
public void display_list(List<Integer> l) {
    int i = 0;
    while (i < l.size()) {
        System.out.println(l.get(i));
        i++;
    }
}
""",
            "recursive": """
import java.util.List;
public void display_list(List<Integer> l) {
    if (l.size() > 0) {
        System.out.println(l.get(0));
        display_list(l.subList(1, l.size()));
    }
}
"""
        },
        "factorial": {
            "for_i": """
public int factorial(int n) {
    int res = 1;
    for (int i = 2; i < n+1; i++) {
        res *= i;
    }
    return res;
}
""",
            "while": """
public int factorial(int n) {
    int res = 1;
    int i = 2;
    while (i <= n) {
        res *= i;
        i++;
    }
    return res;
}
""",
            "recursive": """
public int factorial(int n) {
    if (n < 1) {
        return 1;
    }
    return n * factorial(n-1);
}
"""
        },
        "op_on_element": {
            "op+": """
public int add(int x) {
    return x + 1;
}
""",
            "op*": """
public int mult(int x) {
    return x * 2;
}
""",
            "op<": """
public boolean lower(int x) {
    return x < 0;
}
""",
            "op<=": """
public boolean leq(int x) {
    return x <= 0;
}
""",
            "op>": """
public boolean greater(int x) {
    return x > 0;
}
""",
            "op>=": """
public boolean geq(int x) {
    return x >= 0;
}
""",
            "op==": """
public boolean eq(int x) {
    return x == 0;
}
""",
            "op!=": """
public boolean neq(int x) {
    return x != 0;
}
"""
        },
        "op_on_elements": {
            "op+": """
public int add(int a, int b) {
    return a + b;
}
""",
            "op*": """
public int mult(int a, int b) {
    return a * b;
}
""",
            "op<": """
public boolean lower(int a, int b) {
    return a < b;
}
""",
            "op<=": """
public boolean leq(int a, int b) {
    return a <= b;
}
""",
            "op>": """
public boolean greater(int a, int b) {
    return a > b;
}
""",
            "op>=": """
public boolean geq(int a, int b) {
    return a >= b;
}
""",
            "op==": """
public boolean eq(int a, int b) {
    return a == b;
}
""",
            "op!=": """
public boolean neq(int a, int b) {
    return a != b;
}
"""
        },
        "map": {
            "op+": """
public int[] add(int[] l) {
    int[] res = new int[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] + 1;
    }
    return res;
}
""",
            "op*": """
public int[] mult(int[] l) {
    int[] res = new int[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] * 2;
    }
    return res;
}
""",
            "op<": """
public boolean[] lower(int[] l) {
    boolean[] res = new boolean[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] < 0;
    }
    return res;
}
""",
            "op<=": """
public boolean[] leq(int[] l) {
    boolean[] res = new boolean[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] <= 0;
    }
    return res;
}
""",
            "op>": """
public boolean[] greater(int[] l) {
    boolean[] res = new boolean[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] > 0;
    }
    return res;
}
""",
            "op>=": """
public boolean[] geq(int[] l) {
    boolean[] res = new boolean[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] >= 0;
    }
    return res;
}
""",
            "op==": """
public boolean[] eq(int[] l) {
    boolean[] res = new boolean[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] == 0;
    }
    return res;
}
""",
            "op!=": """
public boolean[] neq(int[] l) {
    boolean[] res = new boolean[l.length];
    for (int i = 0; i < l.length; i++) {
        res[i] = l[i] != 0;
    }
    return res;
}
"""
        },
        "Reduce": {
            "op+": """
public int add(int[] l) {
    int res = 0;
    for (int e : l) {
        res += e;
    }
    return res;
}
""",
            "op*": """
public int mult(int[] l) {
    int res = 1;
    for (int e : l) {
        res *= e;
    }
    return res;
}
"""
        }
    }
}

analogy_types = {
    "for_e": "syntactic",
    "for_i": "syntactic",
    "while": "syntactic",
    "recursive": "syntactic",
    "op+": "semantic",
    "op*": "semantic",
    "op<": "semantic",
    "op<=": "semantic",
    "op>": "semantic",
    "op>=": "semantic",
    "op==": "semantic",
    "op!=": "semantic"
}



if __name__ == "__main__":
    for language in ("python", "java"):
        codes = {}
        analogies = {}
        progs = sorted(programs[language])
        for ip1,prog1 in enumerate(progs):
            for prog2 in progs[ip1+1:]:
                types = sorted(set(programs[language][prog1]).intersection(programs[language][prog2]))
                for it1,type1 in enumerate(types):
                    for type2 in types[it1+1:]:
                        analogy = (programs[language][prog1][type1],
                                   programs[language][prog1][type2],
                                   programs[language][prog2][type1],
                                   programs[language][prog2][type2])
                        analogy_type = analogy_types[type1] if analogy_types[type1]==analogy_types[type2] else "-".join(sorted([analogy_types[type1], analogy_types[type2]]))
                        if not analogy_type in codes:
                            codes[analogy_type] = []
                        for code in analogy:
                            if not code in codes[analogy_type]:
                                codes[analogy_type].append(code)
                        if not analogy_type in analogies:
                            analogies[analogy_type] = []
                        analogies[analogy_type].append(analogy)
        print(language)
        print("nb codes: {} and {}".format(*["{} {}".format(len(codes[analogy_type]), analogy_type) for analogy_type in sorted(codes)]))
        for analogy_type in sorted(analogies):
            print("nb {} analogies: {} (with permutations: {})".format(analogy_type, len(analogies[analogy_type]), 4*len(analogies[analogy_type])))
        print()
