import click

from .data_analysis import generate_cross_corr, ft_selection, pred_diagnostics, cl_pred_diagnostics, model_ft_imp
from .strat import make_new_strat
from .clustering import clustering, simple_era_clustering
from .format_data import data_setup, split_data_clusters
from .prediction import make_prediction, cluster_proba, neutralize_pred, upload_results, compute_predict
from .models import generate_cl_interpo, generate_cl_model, generate_models
from .common import *


@click.group()
def cli():
    return


@cli.command('setup')
def setup():
    data_setup()


@cli.command('corr')
def corr():
    generate_cross_corr()


@cli.command('new')
@click.option(
    "-m",
    "--method",
    type=click.Choice(CLUSTER_METHODS, case_sensitive=False),
    default="cluster",
    prompt=True,
)
@click.argument('folder', type=click.Path(), required=True)
def new(method, folder):
    make_new_strat(method, folder)
    return


@cli.command('ft')
@click.argument('folder', type=click.Path(exists=True))
def ft(folder):
    ft_selection(folder)


@cli.command('cl')
@click.argument('folder', type=click.Path(exists=True))
def cl(folder):
    clustering(folder)
    # elif method == STRAT_ERA_SIMPLE:
    #     simple_era_clustering(folder)
    split_data_clusters(folder)


# TODO : move interpo to train ?
# @cli.command('interpo')
# @click.option("-d", "--debug", default=False, show_default=True, is_flag=True)
# @click.option("-m",
#               "--metrics",
#               default=False,
#               show_default=True,
#               is_flag=True)
# @click.option("-ns",
#               "--no-save",
#               default=True,
#               show_default=True,
#               is_flag=True)
# @click.option("-c", "--cluster", default=None, show_default=True)
# @click.argument('folder', type=click.Path(exists=True))
# def interpo(metrics, debug, no_save, cluster, folder):
#     generate_cl_interpo(folder, metrics, debug, no_save, cluster)


@cli.command('train')
@click.option("-d", "--debug", default=False, show_default=True, is_flag=True)
@click.option("-m",
              "--metrics",
              default=False,
              show_default=True,
              is_flag=True)
@click.option("-ns",
              "--no-save",
              default=False,
              show_default=True,
              is_flag=True)
@click.option("-t",
              "--threadpool",
              default=False,
              show_default=True,
              is_flag=True)
@click.option("-l",
              "--layer",
              type=click.Choice(LAYERS, case_sensitive=False),
              default="fst",
              prompt=True)
@click.option("-c", "--cluster", default=None, show_default=True)
@click.argument('folder', type=click.Path(exists=True))
def train(debug, metrics, no_save, threadpool, layer, cluster, folder):
    save = not no_save
    if layer == '0':
        if cluster is None:
            print("cluster name not provided")
            return
        generate_cl_model(folder, cluster, debug, metrics, save)
    else:
        if cluster is not None:
            print("specifying a cluster is unecessary when training a layer")
        generate_models(folder, layer, debug, metrics, save, threadpool)
    return


@cli.command('mftimp')
@click.option("-m",
              "--metrics",
              default=False,
              show_default=True,
              is_flag=True)
@click.option("-ns",
              "--no-save",
              default=False,
              show_default=True,
              is_flag=True)
@click.option("-l",
              "--layer",
              type=click.Choice(LAYERS, case_sensitive=False),
              default="fst",
              prompt=True)
@click.option("-c", "--cluster", default=None, show_default=True)
@click.argument('models',
                type=click.Choice(MODEL_DICT.keys(), case_sensitive=False),
                default="nn")
@click.argument('folder', type=click.Path(exists=True))
def mftimp(metrics, no_save, layer, cluster, models, folder):

    model_types = ['XGBoost', 'RandomForest', 'NeuralNetwork'
                   ] if models == 'All' else [MODEL_DICT[models]]

    save = not no_save
    if layer == '0':
        if cluster is None:
            print("cluster name not provided")
            return
        model_ft_imp(folder, cluster, model_types, metrics, save)
    else:
        if cluster is not None:
            print("specifying a cluster is unecessary when training a layer")
    return


@cli.command('exec')
@click.option("-t",
              "--threadpool",
              default=False,
              show_default=True,
              is_flag=True)
@click.option("-p",
              "--pred",
              type=click.Choice(PRED_OPERATIONS, case_sensitive=False),
              default="proba",
              prompt=True)
@click.option("-l",
              "--layer",
              type=click.Choice(LAYERS, case_sensitive=False),
              default="fst",
              prompt=True)
@click.option("-c", "--cluster", default=None, show_default=True)
@click.argument('folder', type=click.Path(exists=True))
def exec(threadpool, pred, layer, cluster, folder):
    if pred == 'proba':
        if layer == '0':
            if cluster is None:
                print("cluster name not provided")
                return
            cluster_proba(folder, cluster)
        else:
            if cluster is not None:
                print(
                    "specifying a cluster is unecessary when training a layer")
            if layer == 'snd':
                print("snd layer doesn't produce proba")
            cluster_proba(folder)
    elif pred == 'prediction':
        make_prediction(folder, layer)
    elif pred == 'neutralize':
        neutralize_pred(folder)


@cli.command('compute')
@click.option("-l",
              "--layer",
              type=click.Choice(LAYERS, case_sensitive=False),
              default="fst",
              prompt=True)
@click.option("-c", "--cluster", default=None, show_default=True)
@click.argument('folder', type=click.Path(exists=True))
def compute(layer, cluster, folder):
    compute_predict(layer, cluster, folder)


@cli.command('diag')
@click.option("-l",
              "--layer",
              type=click.Choice(LAYERS, case_sensitive=False),
              default="fst",
              prompt=True)
@click.option("-c", "--cluster", default=None, show_default=True)
@click.argument('folder', type=click.Path(exists=True))
def diag(layer, cluster, folder):
    if layer == '0':
        if cluster is None:
            print("cluster name not provided")
            return
        cl_pred_diagnostics(folder, cluster)
    else:
        if cluster is not None:
            print("specifying a cluster is unecessary for layer diagnostic")
        if layer == 'snd':
            print("snd layer doesn't produce proba")
            return
        pred_diagnostics(folder)


@cli.command('upload')
@click.option("-l",
              "--layer",
              type=click.Choice(LAYERS, case_sensitive=False),
              default="fst",
              prompt=True)
@click.argument('folder', type=click.Path(exists=True))
@click.argument('aggr', type=click.Path(exists=True))
def upload(layer, folder, aggr):
    upload_results(folder, layer, aggr)
