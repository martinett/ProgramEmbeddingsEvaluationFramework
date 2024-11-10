# Program Embeddings Evaluation Framework
A framework to evaluate and compare program embedding spaces. This framework is presented in [martinet et al. 2024](https://ebooks.iospress.nl/doi/10.3233/FAIA240733).

### Requirements
Our implementation is based on a modified version of the gensim library. To use our code, one needs to compile our gensim version first, by running the build_gensim (.sh on ubuntu and .bat on windows). If you want to use our code in another directory, you'll need either to include this project folder in your python path or to move the modified_gensim folder to you python bin folder.  

Our implementation also needs the [tree_sitter library](https://tree-sitter.github.io/tree-sitter) (0.21.0 version).

### Example
Load the model and data modules
```python
from Sec2vec import Sec2vec
from get_data import get_toy_dataset
```
Construct the program list
```python
import numpy as np
programs = [ind["upload"] for ind in data]
exercises = [ind["exercise_name"] for ind in data]
labels = np.unique(exercises, return_inverse=True)[1]
```
Instantiate the model and learn the embeddings
```python
model = Sec2vec(element="token", progrepr="src")
model.train(programs)
embeddings = model.demb.vectors
```
Visualize the embeddings
```python
from sklearn.manifold import TSNE
reductor = TSNE()
emb2d = reductor.fit_transform(embeddings)
plt.scatter(emb2d[:,0], emb2d[:,1], c=labels)
plt.show()
```
Evaluate the embeddings with the clustering index
```python
from metrics import clustering_index
print(clustering_index(embeddings, labels)
```
Evaluate the embeddings with the program analogies
```python
from metrics import analogy_evaluation
embedding_function = lambda program : model.infer(program)[0]
print(analogy_evaluation(embeddings, embedding_function))
```

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
