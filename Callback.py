from modified_gensim.gensim.models.callbacks import CallbackAny2Vec
import os

class Sec2vecCallback:

    def __init__(self, niter, path=".", filename_prefix="", atypical_params={}, name="Sec2vec"):
        self.niter = niter
        self.path = path
        self.filename_prefix = filename_prefix
        self.submodel_name = name
        self.atypical_params = atypical_params

    def get_path(self, ext):
        """Creates the file path, given the epoch number"""
        return "{}/{}_{}_epoch{}".format(self.path, self.submodel_name, self.filename_prefix, self.cur_epoch) + ("" if len(self.atypical_params) == 0 else "".join(["-{}{}".format(p, self.atypical_params[p]) for p in sorted(self.atypical_params.keys())])) + ".{}".format(ext)

    def before_train(self, model):
        self.cur_epoch = 0
        self.effect(model)

    def after_train(self, model):
        self.cur_epoch = self.niter
        self.effect(model)

    def effect(self, model):
        pass


class Sec2vecSaver(Sec2vecCallback):

    def effect(self, model):
        path = self.get_path("sec2vec")
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        model.save(path)


class EpochSaver(CallbackAny2Vec):
    __doc__ = "Callback to save model after each epoch."

    def __init__(self, path=".", filename_prefix="", epoch_end=False, epoch_begin=False, train_end=True, train_begin=True, atypical_params={}):
        self.epoch_end = epoch_end
        self.epoch_begin = epoch_begin
        self.train_end = train_end
        self.train_begin = train_begin
        self.path = path
        self.filename_prefix = filename_prefix
        self.submodel_name = "Sec2vec"
        self.atypical_params = atypical_params
        self.reset()

    def get_path(self, ext):
        """Creates the file path, given the epoch number"""
        return "{}/{}_{}_epoch{}".format(self.path, self.submodel_name, self.filename_prefix, self.cur_epoch) + ("" if len(self.atypical_params) == 0 else "".join(["-{}{}".format(p, self.atypical_params[p]) for p in sorted(self.atypical_params.keys())])) + ".{}".format(ext)

    def set_submodel_name(self, new_name):
        self.reset()
        self.submodel_name = new_name

    def on_train_begin(self, model):
        if self.train_begin:
            self.effect(model)

    def on_epoch_begin(self, model):
        self.cur_epoch += 1
        if self.epoch_begin:
            self.effect(model)

    def on_epoch_end(self, model):
        if self.epoch_end:
            self.effect(model)

    def on_train_end(self, model):
        if self.train_end:
            self.effect(model)

    def effect(self, model):
        """What will be done or saved from the model after each epoch"""
        output_path = self.get_path("model")
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        model.save(output_path)
        model.running_training_loss = 0

    def reset(self):
        self.cur_epoch = 0
