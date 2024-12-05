from prepare_corpus import CorpusBuilder, FullRandomStrategy

from modified_gensim.gensim.models import Doc2Vec
from modified_gensim.gensim.models.doc2vec import TaggedDocument
import numpy as np
from numpy import float32 as REAL

import pickle





class Sec2vec:
    def __init__(self, element="token", progrepr="source", corpus_builder=None,
                 trace_strategy=None, nb_traces=10,
                 language="python", extract_functions=False,
                 anonymize=True, anon_num=False, anon_params=False, anon_comments=True,
                 trainingmodel="pv-dm", aggmode="mean",
                 cwindow=None, vsize=100, niter=50, min_count=1,
                 callbacks=[], sec2vec_callbacks=[], compute_loss=False,
                 seed=1, verbose=False):
        """
        Parameters
        ----------
        element : str, optional
            The level of elements. Must be either "token" or "instruction".
            The default is "token".
        progrepr : str, optional
            The level of instructions. Must be either "source", "trace" or "ast".
            The default is "source".
        trainingmodel : str, optional
            The gensim model to use to learn code representations. Must be
            either "pv-dm", "pv-dbow" or "pv-sg".
            The default is "pv-dm".
        """
        self.verbose = verbose
        self.seed = seed
        
        self.anonymize = anonymize
        self.anon_num = anon_num
        self.anon_params = anon_params
        self.anon_comments = anon_comments
        
        self.element = element
        self.progrepr = progrepr
        self.nb_traces = nb_traces
        self.language = language
        self.extract_functions = extract_functions
        
        if self.progrepr != "ast" and cwindow is None:
            cwindow = 5
        self.cwindow = cwindow
        if progrepr == "ast" and trainingmodel == "pv-sg":
            self.cwindow = 1
        
        self.trace_strategy = trace_strategy or FullRandomStrategy(max_loop=3,
                                                                   seed=seed)
        self.corpus_builder = corpus_builder or CorpusBuilder(
            element=self.element,
            progrepr=self.progrepr,
            language=self.language,
            extract_functions=self.extract_functions,
            cwindow=self.cwindow,
            trace_strategy = self.trace_strategy,
            nb_traces=self.nb_traces,
            anonymize=self.anonymize,
            anon_num=self.anon_num,
            anon_params=self.anon_params,
            anon_comments=self.anon_comments,
            seed=self.seed,
            verbose=self.verbose
        )
        
        self.compute_loss = compute_loss
        self.callbacks = [c for c in callbacks]
        self.sec2vec_callbacks = [c for c in sec2vec_callbacks]
        
        self.trainingmodel = trainingmodel
        self.aggmode = aggmode
        self.vsize = vsize
        self.niter = niter
        
        model_mean = 1 if aggmode=="mean" else 0 if aggmode=="sum" else None
        self.params = {
            "vector_size": self.vsize,
            "min_count": min_count,
            "workers": 1,
            "epochs": self.niter,
            "compute_loss": self.compute_loss,
            "dm_mean": model_mean,
            "dm_concat": int(aggmode=="concat"),
            "dm": trainingmodel in ("pv-dm", "pv-sg"),
            "window_slide": self.trainingmodel != "pv-sg" and self.progrepr != "ast"
        }
        if self.progrepr != "ast":
            if self.trainingmodel == "pv-sg":
                self.params["window"] = 1
            else:
                self.params["window"] = self.cwindow
        
        self.name = "Sec2vec (e={}, s={})".format(self.element[0],
                                                  self.progrepr[0])

        self.wemb = None
        self.demb = None
        self.hemb = None
    
    def train_model(self, corpus, params, wv=None, dv=None, syn1=None,

                      #if True => learn the new and the old,
                      #if False => learn nothing,
                      #if None (default) => learn only the new
                      learn_words=None, learn_tags=None, learn_syn1=None,

                      model_name=None, callbacks=[]):
        if self.verbose:
            if model_name is None:
                model_name = "model"
            print("- {}".format(model_name))
        
        for callback in callbacks:
            callback.set_submodel_name(model_name)
        
        additional_params = {
            "learn_words": learn_words if not learn_words is None else True,
            "learn_syn1": learn_syn1 if not learn_syn1 is None else True
        }
        additional_params["learn_tags"] = \
            learn_tags if not learn_tags is None else True
        if not self.seed is None:
            additional_params["seed"] = self.seed
        
        model = Doc2Vec(**params, **additional_params)
        if self.verbose:
            print("\tBuilding vocab")
        base_corpus = []
        if hasattr(self, "corpus") and self.corpus != corpus:
            base_corpus = self.corpus

        # because at inference, with only the document to infer,
        # the negative sampling will not be efficient with the poor vocab
        model.build_vocab(base_corpus+corpus)
        
        if not wv is None:
            for i in range(len(wv)):
                word = wv.index_to_key[i]
                if word in model.wv:
                    model.wv[word] = wv[word]
        if not dv is None:
            for i in range(len(dv)):
                word = dv.index_to_key[i]
                if word in model.dv:
                    model.dv[word] = dv[word]
        if not syn1 is None:
            for word in syn1:
                if word in model.wv:
                    j = model.wv.key_to_index[word]
                    model.syn1neg[j,:] = syn1[word]
            # for i in range(len(wv)):
            #     word = wv.index_to_key[i]
            #     if word in model.wv:
            #         j = model.wv.key_to_index[word]
            #         model.syn1neg[j,:] = syn1[i,:]
        
        if learn_words is False:
            words_locks = [0.]
        elif learn_words is True:
            words_locks = [1.]
        elif not wv is None:
            words_locks = []
            for i in range(len(model.wv)):
                word = model.wv.index_to_key[i]
                if word in wv:
                    words_locks.append(0.)
                else:
                    words_locks.append(1.)
        else:
            words_locks = [1.]
        
        if learn_tags is False:
            tags_locks = [0.]
        elif learn_tags is True:
            tags_locks = [1.]
        elif not dv is None:
            tags_locks = []
            for i in range(len(model.dv)):
                tag = model.dv.index_to_key[i]
                if tag in dv:
                    tags_locks.append(0.)
                else:
                    tags_locks.append(1.)
        else:
            tags_locks = [1.]
        
        if learn_syn1 is False:
            syn1_locks = [0.]
        elif learn_syn1 is True:
            syn1_locks = [1.]
        elif not syn1 is None:
            syn1_locks = []
            for word in syn1:
                if word in wv:
                    syn1_locks.append(0.)
                else:
                    syn1_locks.append(1.)
            # for i in range(len(model.wv)):
            #     word = model.wv.index_to_key[i]
            #     if word in wv:
            #         syn1_locks.append(0.)
            #     else:
            #         syn1_locks.append(1.)
        else:
            syn1_locks = [1.]
        
        train_params = {
            "total_examples": model.corpus_count,
            "epochs": model.epochs,
            "words_locks": np.array(words_locks, dtype=REAL),
            "syn1_locks": np.array(syn1_locks, dtype=REAL),
            "callbacks": callbacks,
            "compute_loss": self.compute_loss,
            "tags_locks": np.array(tags_locks, dtype=REAL)
        }
        
        if self.verbose:
            print("\tTraining")
        model.train(corpus, **train_params)

        if self.verbose:
            print("Done!")
        return model.dv, model.wv, dict(zip(model.wv.key_to_index.keys(),
                                            model.syn1neg))

    def build_corpus(self, asts):
        corpus = []
        if self.progrepr == "ast":
            for i,ast in enumerate(asts):
                tag = str(i)
                stack = [ast]
                while len(stack) > 0:
                    ast = stack.pop()
                    if self.element == "token":
                        firstword = ast.type
                    elif hasattr(ast, "tokens"): #self.element == "instruction"
                        firstword = "___".join(ast.tokens())
                    else:
                        firstword = "___"
                    words = [firstword]
                    if self.element == "token" and hasattr(ast, "tokens"):
                        words.extend(ast.tokens())
                    childrens = [ast.children()]
                    if hasattr(ast, "get_clauses"):
                        childrens.append(ast.get_clauses())
                    if hasattr(ast, "get_else") and not ast.get_else() is None:
                        childrens.append([ast.get_else()])
                    for children in childrens:
                        for c in children:
                            if (hasattr(c, "tokens") and self.element == "token") or (len(c.children()) > 0) or (hasattr(c, "get_clauses") and len(c.get_clauses()) > 0) or (hasattr(c, "get_else") and not c.get_else() is None):
                                stack.append(c)
                            if self.element == "token":
                                nextword = c.type
                            elif hasattr(c, "tokens"): #self.element == "instruction"
                                nextword = "___".join(c.tokens())
                            else:
                                nextword = "___"
                            words.append(nextword)
                    if self.trainingmodel != "pv-sg":
                        document = TaggedDocument(words, [tag])
                        corpus.append(document)
                    else:
                        for word in words[1:]:
                            document = TaggedDocument([word, words[0]], [tag])
                            corpus.append(document)
        else:
            sequences = [self.corpus_builder.ast2sequence(ast) for ast in asts]
            if self.trainingmodel == "pv-sg":
                for iseq,sequence in enumerate(sequences):
                    for i,element in enumerate(sequence):
                        j = max(0, i-self.cwindow)
                        k = min(len(sequence), i+self.cwindow+1)
                        for i2 in range(j, k):
                            if i2 != i:
                                doc = TaggedDocument([element, sequence[i2]], [str(iseq)])
                                corpus.append(doc)
            else:
                corpus = [TaggedDocument(sequence, [str(iseq)])
                          for iseq,sequence in enumerate(sequences)]
        return corpus

    def get_params(self, corpus):
        params = self.params.copy()
        if self.progrepr == "ast":
            if self.cwindow is None:
                maxsize = 0
                for doc in corpus:
                    size = len(doc[0]) - 1
                    if size > maxsize:
                        maxsize = size
                params["window"] = maxsize
            else:
                params["window"] = self.cwindow
        return params
    
    def train(self, codes=None, asts=None, corpus=None, test_cases=None,
              learn_docs=True):
        """
        Train process on a batch of codes

        Parameters
        ----------
        codes : TYPE
            DESCRIPTION.

        Returns
        -------
        None.
        """
        if codes is None and asts is None and corpus is None:
            raise Exception(
                "You must provide data either as `codes`, `asts` or `corpus`."
            )
        if not codes is None and asts is None and corpus is None:
            asts = []
            for code in codes:
                asts.extend(self.corpus_builder.code2asts(code))
        self.asts = asts

        if corpus is None:
            corpus = self.build_corpus(self.asts)
        
        self.corpus = corpus

        params = self.get_params(corpus)

        for callback in self.sec2vec_callbacks:
            callback.before_train(self)

        self.demb, self.wemb, self.hemb = self.train_model(self.corpus,
                                                   params,
                                                   callbacks=self.callbacks,
                                                   model_name=self.name+" (train1)")
        if learn_docs:
            self.demb, _, _ = self.train_model(self.corpus,
                                               params,
                                               callbacks=self.callbacks,
                                               model_name=self.name+" (train2)",
                                               wv=self.wemb, syn1=self.hemb)

        for callback in self.sec2vec_callbacks:
            callback.after_train(self)
    
        return self.demb.vectors
    
    def infer(self, codes=None, asts=None, corpus=None, test_cases=None):
        """
        Inference process

        Parameters
        ----------
        codes : TYPE
            DESCRIPTION.

        Returns
        -------
        None.
        """
        res = []
        
        if codes is None and asts is None and corpus is None:
            raise Exception(
                "You must provide data either as `codes`, `asts` or `corpus`."
            )
        if not codes is None and asts is None and corpus is None:
            asts = []
            for code in codes:
                asts.extend(self.corpus_builder.code2asts(code))
        
        if corpus is None:
            corpus = self.build_corpus(asts)
        
        dv_names = []
        for doc in corpus:
            for tag in doc[1]:
                if not tag in dv_names:
                    dv_names.append(tag)
        for dv_name in dv_names:
            docs = [doc for doc in corpus if dv_name in doc[1]]
            params = self.get_params(docs)
            
            _, wemb, hemb = self.train_model(docs,
                                             self.params,
                                             callbacks=self.callbacks,
                                             model_name=self.name+" (infer1)",
                                             wv=self.wemb, syn1=self.hemb)
            demb, _, _ = self.train_model(docs,
                                          self.params,
                                          callbacks=self.callbacks,
                                          model_name=self.name+" (infer2)",
                                          wv=wemb, syn1=hemb)
            res.append(demb[dv_name])
        res = np.array(res)
        return res
    
    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self, f)
    
    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            return pickle.load(f)

