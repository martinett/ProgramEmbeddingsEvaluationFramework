import tree_sitter_python as tspython
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
import json, ast, numpy as np, pandas as pd
import os

def NC1014(folder="datasets/"):
    if folder[-1] != "/":
        folder += "/"
    with open(folder+"NewCaledonia_1014.json", "r") as f:
        return [e for e in json.load(f)]
def NC5690(folder="datasets/", exclude=False):
    if folder[-1] != "/":
        folder += "/"
    with open(folder+"NewCaledonia_5690.json", "r") as f:
        return [e for i,e in enumerate(json.load(f)) if not exclude or not i in [305, 2825]]

def PROGPEDIA(language, folder="datasets/"):
    if folder[-1] != "/":
        folder += "/"
    ext = {"python": ".py", "java": ".java"}[language]
    parser = Parser()
    if language == "python":
        lang = Language(tspython.language(), "python")
    elif language == "java":
        lang = Language(tsjava.language(), "java")
    parser.set_language(lang)
    path = folder+"progpedia"
    res = []
    for folder in sorted(os.listdir(path)):
        subpath = path+"/"+folder
        if os.path.isdir(subpath):
            with open(subpath+"/statement.md", "r") as f:
                ex_name = f.readline()
            for category in sorted(os.listdir(subpath)):
                catsubpath = subpath+"/"+category
                if os.path.isdir(catsubpath):
                    for subfolder in sorted(os.listdir(catsubpath)):
                        user = subfolder.split("_")[0]
                        finalfolder = catsubpath+"/"+subfolder
                        if os.path.isdir(finalfolder):
                            files = sorted(os.listdir(finalfolder))
                            for file in files:
                                if file[-len(ext):] == ext:
                                    filepath = finalfolder+"/"+file
                                    try:
                                        with open(filepath, "r") as f:
                                            code = f.read()
                                    except:
                                        with open(filepath, "r", encoding="cp437") as f:
                                            code = f.read()
                                    node = parser.parse(bytes(code, "utf-8")).root_node
                                    if not node.has_error and len(node.children) > 0:
                                        filename = file[:-len(ext)]
                                        ind = {
                                            "upload": code,
                                            "project": folder,
                                            "filename": filename,
                                            "user": user,
                                            "exercise_name": ex_name
                                        }
                                        res.append(ind)
    return res
def PPROGPEDIA(folder="datasets/"):
    return PROGPEDIA("python", folder=folder)
def JPROGPEDIA(folder="datasets/"):
    return PROGPEDIA("java", folder=folder)

def AD2022(language, folder="datasets/"):
    if folder[-1] != "/":
        folder += "/"
    parser = Parser()
    if language == "python":
        lang = Language(tspython.language(), "python")
    elif language == "java":
        lang = Language(tsjava.language(), "java")
    parser.set_language(lang)
    path = folder+"ad2022dataset/AD2022dataset"
    res = []
    years = ["19_20", "20_21", "21_22"]
    for year in years:
        filename = "{}_solutions.csv".format(year)
        filepath = path+"/"+filename
        df = pd.read_csv(filepath, header=0)
        for _,row in df.iterrows():
            if row["question_id"][-len(language):] == language:
                code = row["solution"]
                node = parser.parse(bytes(code, "utf-8")).root_node
                if not node.has_error and len(node.children) > 0:
                    ind = {
                        "upload": code,
                        "user": row["student_id"],
                        "exercise_name": row["question_id"][:-len(language)-1]
                    }
                    res.append(ind)
    return res
def PAD2022(folder="datasets/"):
    return AD2022("python", folder=folder)
def JAD2022(folder="datasets/"):
    return AD2022("java", folder=folder)

