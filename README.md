# Program Embeddings Evaluation Framework
A framework to evaluate and compare program embedding spaces. This framework is presented in [martinet et al. 2024](https://ebooks.iospress.nl/doi/10.3233/FAIA240733).

### Requirements
Our implementation is based on a modified version of the gensim library. To use our code, one needs to compile our gensim version first, by running the build_gensim (.sh on ubuntu and .bat on windows). If you want to use our code in another directory, you'll need either to include this project folder in your python path or to move the modified_gensim folder to you python bin folder.

Our implementation also needs the [tree_sitter library](https://tree-sitter.github.io/tree-sitter) (0.21.0 version).

### Datasets
If you want to reproduce our results, you'll need to download the datasets:
- [NC1014/NC5690 (Cleuziou et Flouvat - 2022)](https://github.com/GCleuziou/code2aes2vec/tree/master/Datasets#datasets-presentation)
- [AD2022 (Petersen-Frey et al. - 2022)](https://www.inf.uni-hamburg.de/en/inst/ab/lt/resources/data/ad-lrec)
- [ProgPedia (Paiva et al. - 2023)](https://zenodo.org/records/7449056)

There is already a python module (get_data.py) to load them.

### Example
Build the tree_sitter language grammar (if using java). You have to do that only once after the installation
```python
from tree_sitter import Language
Language.build_library("build/my-languages.so", ["parsers/tree-sitter-java"])
```
Load the model and data modules
```python
from Sec2vec import Sec2vec
from get_data import NC1014
```
Construct the program list
```python
import numpy as np
data = NC1014()
programs = [ind["upload"] for ind in data]
exercises = [ind["exercise_name"] for ind in data]
```
Instantiate the model and learn the embeddings
```python
model = Sec2vec(element="token", progrepr="source")
model.train(programs)
embeddings = model.demb.vectors
```
Visualize the embeddings
```python
from sklearn.manifold import TSNE
labels = np.unique(exercises, return_inverse=True)[1]
reductor = TSNE()
emb2d = reductor.fit_transform(embeddings)
plt.scatter(emb2d[:,0], emb2d[:,1], c=labels)
plt.show()
```
The code for the other evaluations will be available soon.

### Citation
```
@incollection{martinet2024document,
  title={From document to program embeddings: can distributional hypothesis really be used on programming languages?},
  author={Martinet, Thibaut and Cleuziou, Guillaume and Exbrayat, Matthieu and Flouvat, Fr{\'e}d{\'e}ric},
  booktitle={ECAI 2024},
  pages={2138--2145},
  year={2024},
  publisher={IOS Press}
}
```
