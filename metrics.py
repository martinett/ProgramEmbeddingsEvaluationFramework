from scipy.spatial.distance import cdist, pdist
import numpy as np
from queue import Queue
from threading import Thread
import pandas as pd
import matplotlib.pyplot as plt
from datasets.programs_for_analogies import programs as analogy_programs, analogy_types



def clustering_index(embeddings, labels, verbose=False):
    """
    Performs clustering index evaluation on the given embeddings, following the given information partition (labels).
    
    Parameters
    ----------
    embeddings : np.array
        The embeddings to evaluate.
    labels : np.array
        The labels giving the information partition to check.
    verbose : bool
        Weither to print the steps to monitor the evaluation.
        Default : False

    Returns
    -------
    float
        Clustering index of the given embeddings, following the given information partition.
    """
    embeddings = np.array(embeddings)
    if verbose:
        laststep = None
    total_dist = 0
    intra_dist = 0
    for i in range(len(embeddings)):
        if verbose:
            step = int(i / (len(embeddings) / 100))
            if not laststep is None and step != laststep:
                print((str(step) + "%"), end=" ")
            laststep = step
        p = embeddings[i,:]
        label = labels[i]
        dists = np.sqrt(((p - embeddings[i+1:]) ** 2).sum(axis=1))
        total_dist += dists.sum()
        idx_intra = np.argwhere(labels[i+1:] == label)[:,0]
        intra_dist += dists[idx_intra].sum()
    if verbose:
        print()
    return intra_dist / total_dist




def analogy_test(T, a, a_, b, b_, maxdist, k=1, distance="euclidean", exclude_terms=False):
    """
    Try an analogy (a:a_ = b:b_) on a KeyedVectors-like format embeddings of a model.

    Parameters
    ----------
    T : dict<int,np.array>
        The embeddings to check the analogy on, with each embedding retrievable with an int id.
    a : int
        The id of the first analogy operand.
    a_ : int
        The id of the second analogy operand.
    b : int
        The id of the third analogy operand.
    b_ : int
        The id of the fourth analogy operand.
    maxdist : float
        The maximum distance between two embeddings in T (to normalize the embeddings)
    k : int, optional
        The number of nearest neighbors to observe.
        The default is 1.
    distance : str, optional
        The distance to compare the embeddings with.
        The default is "euclidean".
    exclude_terms : bool, optional
        If true, the analogy will be evaluated after having excluded its terms from T.
        The default is False.

    Returns
    -------
    int or None
        1 if the analogy has been validated in the k nearest neighbors, 0 otherwise, or None if not all the analogy operands are present in T.

    """
    if a in T and a_ in T and b in T and b_ in T:
        v = T[b]-T[a]+T[a_]
        keys = [e for e in T if not exclude_terms or not e in (a,a_,b)]
        vectors = [T[e] for e in keys]
        dists = cdist([v], vectors, metric=distance)[0]
        idxsort = np.argsort(dists)
        keys = [keys[i] for i in idxsort]
        bs = keys[:k]
        found = b_ in bs
        return found
    else:
        return None




def analogy_evaluation(embeddings, embfunc, language="python",
                       distance="euclidean", k=1,
                       permute_analogies=True, exclude_terms=False,
                       workers=1, verbose=False):
    """
    Performs program analogy evaluation on the given embeddings.
    
    Parameters
    ----------
    embeddings : np.array
        The embeddings to evaluate.
    embfunc : function(str):np.array
        A function that compute the embedding of a program, using the model that built the given embeddings.
    distance : str
        Used distance to compare program embeddings.
        Must be either "euclidean" or "cosine".
        Default : "euclidean"
    language : str
        Programming language in which the programs corresponding to the given embeddings were written.
        Must be either "python" or "java".
        Default : "python"
    k : int
        Number of nearest neighbors to observe to search for the analogy targets.
        Must be greater than 0.
        Default : 1
    permute_analogies : bool
        Weither to permute the analogies in order to evaluate more embedding space or not.
        Default : True.
    exclude_terms : bool
        Weither to exclude the analogy terms of the observed nearest neighbors or not.
        Default : False
    workers : int
        Number of workers to perform the analogies in parallel.
        Must be greater than 0.
        Default : 1
    verbose : bool
        Weither to print the steps to monitor the evaluation.
        Default : False

    Returns
    -------
    dict<str,int>
        Analogy accuracy of the given embeddings, for each analogy type.
    """
    ltypes = sorted(analogy_types)
    analogies = []
    analogytypes = []
    posstypes = []
    fnames = sorted(analogy_programs[language])
    codes = [analogy_programs[language][fname][ltype] for fname in fnames for ltype in ltypes if ltype in analogy_programs[language][fname]]
    for if1,fname1 in enumerate(fnames):
        for if2,fname2 in enumerate(fnames[if1+1:]):
            for il1,ltype1 in enumerate(ltypes):
                if ltype1 in analogy_programs[language][fname1] and ltype1 in analogy_programs[language][fname2]:
                    for il2,ltype2 in enumerate(ltypes[il1+1:]):
                        if ltype2 in analogy_programs[language][fname1] and ltype2 in analogy_programs[language][fname2]:
                            #analogytype = "-".join(sorted((ltype1, ltype2)))
                            analogytype = analogy_types[ltype1] if analogy_types[ltype1] == analogy_types[ltype2] else "-".join(sorted([analogy_types[type1], analogy_types[type2]]))
                            if not analogytype in posstypes:
                                posstypes.append(analogytype)
                            f11 = analogy_programs[language][fname1][ltype1]
                            f12 = analogy_programs[language][fname1][ltype2]
                            f21 = analogy_programs[language][fname2][ltype1]
                            f22 = analogy_programs[language][fname2][ltype2]
                            analogy = tuple(codes.index(code) for code in (f11,f12,f21,f22))
                            analogies.append(analogy)
                            analogytypes.append(analogytype)
                            if permute_analogies:
                                per1 = analogy[2:]+analogy[:2]
                                per2 = analogy[1::-1]+analogy[:1:-1]
                                per3 = analogy[::-1]
                                analogies.extend((per1,per2,per3))
                                analogytypes.extend([analogytype]*3)

    counts = {atype: 0 for atype in posstypes}
    total = {atype: 0 for atype in posstypes}
    vectors = [embfunc(code) for code in codes]
    vectors = np.concatenate((vectors, embeddings))
    
    T = dict(zip(range(len(vectors)), list(vectors)))
                    
    q = Queue()
    maxdist = pdist(vectors, metric=distance).max()

    def crawl(q):
        while not q.empty():
            i, analogy = q.get()
            try:
                res = analogy_test(T, *analogy, maxdist,
                                   k=k, distance=distance,
                                   exclude_terms=exclude_terms)
                if not res is None:
                    counts[analogytypes[i]] += int(res)
                    total[analogytypes[i]] += 1
            except:
                print("Error")
            if verbose and i%100==0:
                print("{}/{}".format(i, len(analogies)), flush=True)
            q.task_done()
        return True

    for i,analogy in enumerate(analogies):
        q.put((i, analogy))
    for i in range(workers):
        worker = Thread(target=crawl, args=(q,))
        worker.daemon = True
        worker.start()
    q.join()

    for atype in counts:
        counts[atype] /= total[atype]

    if verbose:
        print("{}/{}".format(len(analogies[language]), len(analogies[language])), flush=True)
        print()
        print(distance)
        print(counts)
        print()

    return counts
