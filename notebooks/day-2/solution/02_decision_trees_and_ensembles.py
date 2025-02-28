# -*- coding: utf-8 -*-
"""02-decision_trees_and_ensembles.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/yandexdataschool/mlhep2019/blob/master/notebooks/day-2/02_decision_trees_and_ensembles.ipynb

# Plan for the seminar
* Warm up: decision trees - their strengths and limitations
* Moving slowly to real world - bagging ensembles
* An interlude on uncertainty
* Heavy duty maching learning - gradient boosting machines

# Decision Trees
![Decision tree joke](https://camo.githubusercontent.com/08b9d1f7280425a77ddf445fb40dc1e0827ea44a/68747470733a2f2f7062732e7477696d672e636f6d2f6d656469612f4231336e3256564349414130684a532e6a7067)

// Based on our [course at ICL](https://github.com/yandexdataschool/MLatImperial2019-private/blob/master/04_lab/lab4_trees_ensambling_stacking.ipynb) and [MLHEP 2018](https://github.com/yandexdataschool/mlhep2018/blob/master/day1-Mon/seminar-02-tree-ensembles-1-bagging-xgboost-Solution.ipynb)
"""

# %matplotlib inline
import numpy as np
import matplotlib.pyplot as plt

"""Generating a toy dataset with 2 features for binary classification:"""

from sklearn.datasets import make_blobs

X_toy, y_toy = make_blobs(n_samples=400,
                          centers=[[0., 1.], [1., 2.]],
                          random_state=14)

plt.scatter(X_toy[:, 0], X_toy[:, 1], c=y_toy, alpha=0.8, cmap='bwr')
plt.xlabel('X1'), plt.ylabel('X2');

"""## Enter Decision Tree"""

from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

"""Key parameters:
* `max_depth` – a limit on tree depth (default – no limit)
* `min_samples_split` – there should be at least this many samples to split further (default – 2)
* `min_samples_leaf` – there should be at least this many samples on one side of a split to consider it valid (default – 1).
* `criterion` – the function to measure the quality of a split. Supported criteria are “gini” for the Gini impurity and “entropy” for the information gain.
"""

from sklearn.metrics import accuracy_score
import matplotlib
def plot_decision_surface(clf,
                          X: np.ndarray,
                          y: np.ndarray,
                          grid_step: float=0.02,
                          cmap='bwr',
                          alpha:float=0.6,
                          axes=None
        ):
    """
    Plot the decision surface of a classifier, visualize selected points
    Args:
      clf: a fitted model, must support predict method
      X[n_examples, n_features]: points where to evaluate the classifier
      y[n_examples]: true labels
      grid_step: decision surface plottting grid
      alpha: opacity of the decision surface
      axes(matplotlib.axes._subplots.AxesSubplot): axes where plot, if None, a new figure is created
    """
    
    # Define the grid
    x_top_left = X.min(axis=0) - 1
    x_bottom_right = X.max(axis=0) + 1
    grid_x0, grid_x1 = np.meshgrid(
         np.arange(x_top_left[0], x_bottom_right[0], grid_step),
         np.arange(x_top_left[1], x_bottom_right[1], grid_step)
      )
    
    # Calculate predictions on the grid
    y_pred_grid = clf.predict(
                        np.stack(
                              [
                                grid_x0.ravel(),
                                grid_x1.ravel()
                              ],
                              axis=1
                            )
                      ).reshape(grid_x1.shape)
    
    # Find optimal contour levels and make a filled
    # contour plot of predictions
    labels = np.sort(np.unique(y))
    labels = np.concatenate([[labels[0] - 1],
                             labels,
                             [labels[-1] + 1]])
    medians = (labels[1:] + labels[:-1]) / 2
    if axes is None:
      _, axes = plt.subplots()
    axes.contourf(grid_x0, grid_x1, y_pred_grid, cmap=cmap, alpha=alpha,
                 levels=medians)
    
    # Scatter data points on top of the plot,
    # with different styles for correct and wrong
    # predictions
    y_pred = clf.predict(X)
    axes.scatter(*X[y_pred==y].T, c=y[y_pred==y],
                marker='o', cmap=cmap, s=10, label='correct')
    axes.scatter(*X[y_pred!=y].T, c=y[y_pred!=y],
                marker='x', cmap=cmap, s=50, label='errors')

    # Dummy plot call to print the accuracy in the legend.
    axes.plot([], [], ' ',
             label='Accuracy = {:.3f}'.format(accuracy_score(y, y_pred)))
    axes.legend(loc='best')

clf = DecisionTreeClassifier(min_samples_leaf=30).fit(X_toy, y_toy)
fig, ax = plt.subplots(figsize=(5, 5))
plot_decision_surface(clf, X_toy, y_toy, axes=ax)

"""As promissed, trees can be visualized"""

import sklearn.tree

fig, ax = plt.subplots(figsize=(15, 15))
sklearn.tree.plot_tree(clf, ax=ax);

"""An important piece of API for sklearn and the majority of ML packages:"""

# predict returnes class labels, for binary classification they are in {0, 1}
clf.predict(X_toy) # np.ndarray[n_exmples]

# predict_proba returns probabilities for each class
# for many methods, they are not well-calibrated
# see https://scikit-learn.org/stable/modules/calibration.html for calibration methods
clf.predict_proba(X_toy) # np.ndarray[n_examples, n_classes]

"""Let's load the multiclassification toy data and then continue to the tasks"""

! wget https://github.com/yandexdataschool/mlhep2018/raw/master/day1-Mon/data.npz

muticlass_toy_data = np.load("data.npz")
X_toy_multiclass_train, X_toy_multiclass_test, \
  y_toy_multiclass_train, y_toy_multiclass_test = \
    train_test_split(muticlass_toy_data["X"], muticlass_toy_data["y"],
                     test_size=0.5, random_state=1337)

X_toy_train, X_toy_test, y_toy_train, y_toy_test = \
    train_test_split(X_toy, y_toy, test_size=0.25, random_state=42)

"""### Task 1 (difficulty: easy)
Now it's your turn to investigate how the decision boundary depends on the tree depth. Maximum tree depth is defined by the `max_depth` parameter. Try out the following values: ``[1, 2, 3, 5, 10]``. Make decision boundary plots for both train and test datasets (separately).
"""

depth_values = [1, 2, 3, 5, 10]

fig, axes_matrix = plt.subplots(nrows=len(depth_values), ncols=2,
                                figsize=(2*5, 5*len(depth_values)))
for depth, (axes_train, axes_test) in zip(depth_values, axes_matrix):
  ### Write your code here ###
  # The boilerplate code is the elegant way to get a grid of plots in matplotlib
  # All you need is to fit a decision tree and call plot_decision_surface
  # axes_train and axes_test for train and test plots correspondingly
  clf = DecisionTreeClassifier(max_depth=depth).fit(X_toy_train, y_toy_train)
  plot_decision_surface(clf, X_toy_train, y_toy_train, axes=axes_train)
  plot_decision_surface(clf, X_toy_test, y_toy_test, axes=axes_test)
  pass

"""### Task 2 (difficulty: moderate)
We need a better tree!

Try adjusting the parameters of DecisionTreeClassifier to improve the test accuracy for the multiclassification problem.

    Accuracy >= 0.72 - not bad for a start
    Accuracy >= 0.75 - better, but not enough
    Accuracy >= 0.77 - pretty good
    Accuracy >= 0.78 - great! (probably the best result for a single tree)

Feel free to modify the DecisionTreeClassifier below instead of re-writing everything.
"""

# Train a classifer
clf = DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, criterion='gini')
clf.fit(X_toy_multiclass_train, y_toy_multiclass_train)

# Plot the decision surface on the test data
# Note the accuracy number in top-right corner
fig, ax = plt.subplots(figsize=(8, 8))
plot_decision_surface(clf, X_toy_multiclass_test, y_toy_multiclass_test, cmap='rainbow', grid_step=0.2, axes=ax);

"""## Decision trees conclusion
Key advantages:
* Interpretable results
* Not sensitive to data scaling
* Natural support for missing values and categorial data

Key disadvanatages:
* (comparatively) poor quality of the result
* Unstable training - small variations in the data might result in a completely different tree being generated

# Ensembles warm up: Random Forest
Random forest fits multiple trees on random subsets of examples and features. They are better than raw decision trees almost in every respect - with the exception of interpretability.

Compared to boosting, the advantages are:
* Harder to overfit. Overfitting will not be made worse by adding more trees. Question to you: why?
* Very easy to implement parallel training. If you ever have to do it by yourself for whatever reason...

Compared to boosting, the disadvantage is worse quality.

Please take your time to enjoy the beatiful smooth decision surface:
"""

from sklearn.ensemble import RandomForestClassifier

# Note the n_jobs parameter: it defines the number of parallel training processes
# -1 means to use all available
random_forest = RandomForestClassifier(n_estimators=100,
                                       min_samples_leaf=5,
                                       n_jobs=-1)

random_forest.fit(X_toy_multiclass_train, y_toy_multiclass_train)

fig, ax = plt.subplots(figsize=(8, 8))
plot_decision_surface(random_forest,
                      X_toy_multiclass_test,
                      y_toy_multiclass_test,
                      cmap='rainbow', grid_step=0.4, axes=ax)

"""# An interlude on uncertainty
*  Quality of an ML algorithm "in general" is hard to define and, in complete absense of assumptions on the data, all algorithms have the same performance - [no free lunch theorem](https://en.wikipedia.org/wiki/No_free_lunch_theorem)
*  Performance of a **particular** trained model on a **particular** test dataset is, however, a simple statistical problem you all are familiar with. Example loss is an i. i. d. random variable, algorithm performance is its expeted value, this is it.
* As AUC is not an expectation of some **per-example** loss, the statistics is a lot trickier. See the [paper](https://ieeexplore.ieee.org/document/6851192/) and a [python implementation](https://github.com/yandexdataschool/roc_comparison/)

## Task 3 (difficulty: statistics 101)
Compute the t-statistic and p-value and for hypothesis that random forest average accuracy is equal to decision tree accuracy on the `toy_multiclass_test` dataset
* for the whole test dataset
* for a subset of 5 examples
"""

predictions_forest = random_forest.predict(X_toy_multiclass_test)
predictions_tree = DecisionTreeClassifier().fit(
    X_toy_multiclass_train, y_toy_multiclass_train).predict(X_toy_multiclass_test)

### Write your code here ###
# Your good friends here are
# - the definition of accuracy mean(predicted_label == real_label)
# - T-test and its Python implementation: scipy.stats.ttest_ind
import scipy
accuracy_tree = (predictions_tree == y_toy_multiclass_test)
accuracy_forest = (predictions_forest == y_toy_multiclass_test)
scipy.stats.ttest_ind(accuracy_tree, accuracy_forest)
N = 10
scipy.stats.ttest_ind(accuracy_tree[:N], accuracy_forest[:N])

"""# Something you'll actually use: Gradient Boosting machines
From user point of view the competing toolkits are largely the same. Think BMW vs. Mercedes or Tensorflow 2 vs pytorch. In each there is clever engeneering, smart algorithm enchantments and ingenious heuristic tricks, but for common tasks the performance difference is different from paper to paper and is small for practical purposes.

They all support **multithreading**, training on **GPU**,  have commited developer communities, **documentation**, and, subjectively, are great pieces of software. As of 2019 in chronological order:

### XGBoost
* Is the oldest and the most known
* Multi-node Multi-GPU distributed training
* Can [plot its trees](https://xgboost.readthedocs.io/en/latest/python/python_api.html#module-xgboost.plotting)

#### Notable technical details [[paper](https://arxiv.org/pdf/1603.02754.pdf)]:
* Can use [DART: Dropouts meet Multiple Additive Regression Trees](http://proceedings.mlr.press/v38/korlakaivinayak15.pdf)
* Can use exact, approximate and histogram-based split search

### Light GBM
* (supposingly) Fast and memory-efficitent training
* GPU training
* [Distributed training](https://github.com/microsoft/LightGBM/blob/master/docs/Parallel-Learning-Guide.rst)

#### Notable [technical details](https://github.com/microsoft/LightGBM/blob/master/docs/Features.rst) [[paper](https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree.pdf)]
* Gradient-based One-Side Sampling (GOSS)
* Exclusive Feature Bundling (EFB). 
* LightGBM uses histogram-based algorithms, which bucket continuous feature (attribute) values into discrete bins
* Leaf-wise (Best-first) Tree Growth

### Catboost
* Built-in handling of categorial features
* Single-node Multi-GPU training
* Is fast to run the prediction (we use in LHCb trigger)
* [Fancy Jupyter training visualisation](https://catboost.ai/docs/features/visualization.html) (sadly, doesn't work in colab)

#### Notable technical details [[paper](https://arxiv.org/pdf/1706.09516.pdf)]:
* Uses oblivious trees. They are less flexible than the ordinary trees, but are a lot faster to evaluate

![oblivious trees](https://github.com/yandexdataschool/mlhep2019/raw/master/notebooks/day-2/oblivious_tree.webp)

* Ordered boosting: for calculating the residual on an example, uses a model trained without it
* Uses histogram-based split selection

# Primer on Gradient boosting
Install a GPU-enabled version of lightgbm. Might take a couple of minutes.
"""

! pip install lightgbm --no-deps  --upgrade --force-reinstall --install-option=--gpu

"""Install catboost"""

! pip install catboost

"""Get the Higgs dataset (again, takes 2-5 minutes)"""

! wget https://archive.ics.uci.edu/ml/machine-learning-databases/00280/HIGGS.csv.gz

import numpy as np
from sklearn.metrics import roc_auc_score

data = np.genfromtxt("HIGGS.csv.gz", 
                     delimiter=",", dtype=np.float32, max_rows=300000)
X, y = data[:, 1:], data[:, 0]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=200000)
X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, test_size=100000)

import catboost
import xgboost
import lightgbm

"""GPU models:"""

models_gpu = {
    "catboost": catboost.CatBoostClassifier(verbose=False, task_type='GPU'),
    "xgboost": xgboost.XGBClassifier(tree_method="gpu_hist"),
    "lightgbm": lightgbm.LGBMClassifier(device_type="gpu")
}

"""CPU models:"""

models_cpu = {
    "catboost": catboost.CatBoostClassifier(verbose=False, thread_count=-1),
    "xgboost": xgboost.XGBClassifier(tree_method="hist", thread_count=-1),
    "lightgbm": lightgbm.LGBMClassifier(thread_count=-1)
}

"""Will show "GPU memory usage is close to the limit" - this is expected, catboost allocates all available GPU memory"""

import time
def evaluate_models(models_dict):
  for model_name, model in models_dict.items():
    start = time.time()
    model.fit(X_train, y_train)
    end = time.time()
    print("{}; train time {:.3f} s; ROC AUC = {:.3f}".format(
          model_name,
          end - start,
          roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])))

evaluate_models(models_gpu)

evaluate_models(models_cpu)

"""## A note on parameter tuning
In a nutshell, parameter tuning is about bias-variance tradeoff. You tune strength of different regularizations - make model more flexible and more likely to overfit and visa versa. Cross-validation (or just holdout set validation) is your best friend here.

The most important parameter usually are learning rate and the number of iterations. You want to specify the model complexity you can afford and then fully utilize said complexity.

Next in importance, according to the authors of the libararies, are the regularizations, such as L2 and tree depth.

We don't have time to thoroughly discuss all options of all packages - if you are interested in parameter tuning, please read the documentation of the library of choice: [xgboost](https://xgboost.readthedocs.io/en/latest/tutorials/param_tuning.html), [lightgbm](https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html), [catboost](https://catboost.ai/docs/concepts/parameter-tuning.html)

You don't have to tune the parameters manually! Just stay with us till the next Monday and the balck box optimization.

P. S.
Please note a sad peculiarity of XGBoost API: it will not complain when passed invalid parameters
"""

xgboost.XGBClassifier(n_eSStimators=666)

"""## Task 4 (difficulty: semi-real life)
The above train time comparison is not fair. We just ran training with default parameters - it is always possible that, if we take more iterations for some models and less for others, both timing and discrimination performances would arrange themselves differently. Your task is to do a fair comparison.

### Task 4.1
Plot the ROC AUC as function of training time for different libraries, by varying just the number of iterations, leaving all other parameters to default values. Explore interations count in `np.logspace(1, 4, num=6, base=10, dtype=np.int32)`
"""

### Write your code here ###
for count in np.logspace(1, 4, num=6, base=10, dtype=np.int32):

"""### Task 4.2 (Bonus)

Write a function that selects the optimal learning rate. Early stopping is your good friend here: if a model has reached the maximum quality before hitting the iterations limit, the learning rate can be decreased, otherwise increased.
"""

# xgboost
eval_set = [(X_val, y_val)]
model_xgb = xgboost.XGBClassifier(n_estimators=100500,
                                  tree_method="gpu_hist", # No reason not to
                                  learning_rate=1.) # So that in this example it will quickly overfit
model_xgb.fit(X_train, y_train,
              verbose=False,
              eval_metric="auc", # We use that metric for final scoring
              early_stopping_rounds=10, # Try training this more rounds after reaching the best score
              eval_set=eval_set) # Note that we use separate datasets for test and early stopping
print("The trained model has only {} trees".format(len(model_xgb.get_booster().get_dump())))

# lightgbm
model_lgb = lightgbm.LGBMClassifier(n_estimators=100500,
                                    device_type="gpu",
                                    learning_rate=1.)
model_lgb.fit(X_train, y_train,
              verbose=False,
              eval_metric="auc",
              early_stopping_rounds=10,
              eval_set=eval_set)

print("The trained model has only {} trees".format(
      model_lgb.booster_.num_trees()))

# catboost
model_cb = catboost.CatBoostClassifier(n_estimators=100500,
                                       verbose=False, task_type='GPU',
                                       learning_rate=1.,
                                       # Note how unlike the other packages
                                       # eval_metric is passed to constructor
                                       # instead of fit method
                                       eval_metric="AUC")

model_cb.fit(X_train, y_train,
              verbose=False,
              early_stopping_rounds=10,
              eval_set=eval_set)
print("The trained model has only {} trees".format(
      model_cb.tree_count_))

# When a function gets a model in parameters, it will be reference
# it would be bad style to change it, so here is how to make a copy
from sklearn.base import clone
model_copy = clone(model_cb)

### Write your code here ###

"""### Task 4.3 (Bonus)
Use the learning rate tuning function to plot the score vs. train time curve (like in the task 3.1), but for each number of iterations use the optimal learning rate. This WILL take computational time, just like most comprehensive machine learning studies - after making sure the code works, you may want to persist some results on Google Drive.
"""

### Write your code here ###

"""# Ensembling - recap
* Combining several models in a semi-clever way usually results in better quality
* The most common ways are stacking, bagging and boosting
* Stacking is how deep learning works - by using the output of one model  as features to another.
* Stacking is a common thing in competititive data science, where it allows to get that 0.0001%. A common quick and dirty technique of averaging predictions of different models can be viewed as stacking with a linear model.
* Boosted decision trees have quality competitive with deep learning on tabular data. In general (please don't quote me on this), there is a trend that the smaller the datasets, the worse will a fully-connected MLP perform when compared to gradient boosting. //Tabular here means without assumptions of structure in featueres, such as when they pixels in an image. E. g. [Higgs dataset](https://archive.ics.uci.edu/ml/datasets/HIGGS) is tabular, but ImageNet is not. You can treat any dataset as tabular, but almost certainly ignoring the structure will lead to worse performance.
"""