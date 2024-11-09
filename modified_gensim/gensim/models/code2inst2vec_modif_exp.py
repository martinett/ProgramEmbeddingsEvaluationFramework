import numpy as np
from code2aes2vec.manage import jsonAttempts2data, jsonExercises2data
from code2inst2vec import Code2inst2vec

frozen = False
dataset_name = "nc1014"


if dataset_name == "nc1014":
    raw_data = [e for e in jsonAttempts2data('code2aes2vec/Datasets/NewCaledonia_1014.json')]
elif dataset_name == "nc5690":
    raw_data = [e for i,e in enumerate(jsonAttempts2data('datasets/NewCaledonia_5690.json')) if not i in [305, 2825]]
exs = jsonExercises2data('code2aes2vec/Datasets/NewCaledonia_exercises.json')
dataset = [e["upload"] for e in raw_data]
test_cases = [exs[ind["exercise_name"]]["entries"] for ind in raw_data]
models = {"normal": Code2inst2vec(frozen_insts=frozen, verbose=True),
          "sans_nums": Code2inst2vec(anon_num=False, frozen_insts=frozen, verbose=True),
          "tout_var": Code2inst2vec(anon_params=False, frozen_insts=frozen, verbose=True),
          "tout_var_sans_nums": Code2inst2vec(anon_num=False, anon_params=False, frozen_insts=frozen, verbose=True)}

learning_code_insts=None
learning_traces=None
learning_insts=None
for model_name in models:
    model = models[model_name]
    code_insts, traces = model.train(dataset, test_cases,
                                     code_insts=learning_code_insts, traces=learning_traces, insts=learning_insts)
    if learning_code_insts is None:
        learning_code_insts = code_insts
    if learning_traces is None:
        learning_traces = traces
    if learning_insts is None:
        learning_insts = model.insts

code_base = """def indiceOccurrence(n,x,l):
  trouve=False
  i=0
  cpt=0
  while i<len(l) and not trouve:
    if l[i]==x:
      cpt+=1
    if cpt==n:
      trouve=True
    i+=1
  if trouve:
    res=i-1
  else:
    res=None
  return res
"""
code_lvl1 = """def indiceOccurrence(n,x,l):
  trouve=False
  i=0
  cpt=0
  res=0
  while i<len(l) and not trouve:
    if l[i]==x:
      cpt+=1
    if cpt==n:
      trouve=True
    i+=1
  if trouve:
    res=i-1
  else:
    res=None
  return res
"""
code_lvl2 = """def indiceOccurrence(n,x,l):
  trouve=False
  i=0
  cpt=0
  var=0
  while i<len(l) and not trouve:
    if l[i]==x:
      cpt+=1
    if cpt==n:
      trouve=True
    i+=1
  if trouve:
    res=i-1
  else:
    res=None
  return res
"""
code_lvl3 = """def indiceOccurrence(n,x,l):
  trouve=False
  cpt=0
  i=0
  while i<len(l) and not trouve:
    if l[i]==x:
      cpt+=1
    if cpt==n:
      trouve=True
    i+=1
  if trouve:
    res=i-1
  else:
    res=None
  return res
"""
code_lvl4 = """def indiceOccurrence(n,x,l):
  trouve=False
  i=0
  cpt=0
  while not trouve and len(l)>i:
    if l[i]==x:
      cpt+=1
    if cpt==n:
      trouve=True
    i+=1
  if trouve:
    res=i-1
  else:
    res=None
  return res
"""
code_lvl5 = """def indiceOccurrence(n,x,l):
  trouve=False
  i=0
  cpt=0
  if trouve:
    res=i-1
  else:
    res=None
  while i<len(l) and not trouve:
    if l[i]==x:
      cpt+=1
    if cpt==n:
      trouve=True
    i+=1
  return res
"""
modif_lvls = ["base", "assign_add_1", "assign_add_2", "assign_inv", "condition_inv", "bloc_inv"]
codes = {"base": code_base,
         "assign_add_1": code_lvl1,
         "assign_add_2": code_lvl2,
         "assign_inv": code_lvl3,
         "condition_inv": code_lvl4,
         "bloc_inv": code_lvl5}
modif_dataset = dataset + [codes[modif_lvl] for modif_lvl in modif_lvls]
test_case = [(3, 12, [12, 3, 4, 12, 8, 12, 5, 12]),
             (2, 8, [12, 3, 4, 12, 8, 12, 5, 12]),
             (1, 12, []),
             (4, 12, [12, 3, 4, 12, 8, 12, 5, 12]),
             (1, 12, [12, 3, 4, 12, 8, 12, 5, 12]),
             (4, 7, [12, 3, 4, 12, 8, 12, 5, 12]),
             (-3, 12, [12, 3, 4, 12, 8, 12, 5, 12])]
modif_test_cases = test_cases + [test_case]*len(codes)
infer_code_insts = None
infer_traces = None
infer_insts = None
embeddings = {}
for model_name in models:
    model = models[model_name]
    if infer_code_insts is None:
        infer_code_insts = model.construct_insts_dict(modif_dataset)
    if infer_traces is None:
        infer_traces = model.compute_traces(modif_dataset, modif_test_cases, infer_code_insts)
    if infer_insts is None:
        infer_insts = model.insts
    embeddings[model_name] = model.infer(modif_dataset, modif_test_cases,
                                         code_insts=infer_code_insts, traces=infer_traces, insts=infer_insts)






exs_list = [e["exercise_name"] for e in raw_data]
ex_ids = np.unique(exs_list)
ex_nos = np.array([np.where(ex_ids==e)[0][0] for e in exs_list])

from sklearn.manifold import TSNE
proj = {}
for model_name in models:
    reductor = TSNE()
    proj[model_name] = reductor.fit_transform(np.array(embeddings[model_name]))

import matplotlib.pyplot as plt
for model_name in models:
    plt.figure()
    plt.scatter(proj[model_name][:len(exs_list),0], proj[model_name][:len(exs_list),1], c=ex_nos)
    xscale = proj[model_name][:,0].max() - proj[model_name][:,0].min()
    yscale = proj[model_name][:,1].max() - proj[model_name][:,1].min()
    for i in range(len(modif_lvls)):
        if i>0:
            plt.plot(proj[model_name][(len(exs_list),len(exs_list)+i),0], proj[model_name][(len(exs_list),len(exs_list)+i),1], c="black")
        plt.text(proj[model_name][len(exs_list)+i,0]+xscale/200, proj[model_name][len(exs_list)+i,1]+yscale/200, modif_lvls[i])
    plt.show()








for model_name in models:
    fig,(ax,tax) = plt.subplots(ncols=2)
    sc = ax.scatter(proj[model_name][:len(exs_list),0], proj[model_name][:len(exs_list),1], c=ex_nos)
    txt = tax.text(0, 1, "", verticalalignment="top")
    plt.sca(tax)
    plt.xticks([], [])
    plt.yticks([], [])

    def hover(event):
        if event.inaxes == ax:
            cont, ind = sc.contains(event)
            if cont:
                i = ind["ind"][0]
                txt.set_text(raw_data[i]["upload"])
                fig.canvas.draw_idle()
            else:
                if txt.get_text() != "":
                    txt.set_text("")
                    fig.canvas.draw_idle()
        else:
            if txt.get_text() != "":
                txt.set_text("")
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

    plt.show()