import argparse
import sys
import time
from collections import deque

from common import *
from data_analysis import feature_era_corr
from clustering import clustering, clustering_2, simple_era_clustering
from format_data import split_data_clusters
from feature_analysis import ft_target_mut_i, ft_selection, eras_mut_info
from models import generate_models, generate_cl_model
from reader import set_h5_stores
from prediction import make_prediction, cluster_proba, snd_layer_training_data, upload_results

ALL_OPERATIONS = [
    'h5', 'ft_era_corr', 'ft_sel', 'mut_i', 'set_data', 'train', 'proba',
    'prediction', 'upload'
]


def print_funct_calls(layers, strategies, operations_q):
    l_aux = layers.copy()
    s_aux = strategies.copy()
    o_aux = operations_q.copy()

    while 0 < len(o_aux):
        op = o_aux.popleft()
        print("op: ", op)

        if op == 'h5':
            print('   --> set_h5_stores')
            continue

        for stra in s_aux:
            print(" strat: ", stra)
            for l in l_aux:
                print('  layer: ', l)
                if op == 'ft_sel':
                    print('   --> ft_sel')
                    continue

                if op == 'mut_i':
                    print('   --> mut_i')
                    continue

                if op == 'proba':
                    print('   --> make_proba')
                    continue
                if op == 'prediction':
                    print('   --> make_pred')
                    continue
                if op == 'train':
                    print('   --> generate_models')
                    continue

                if op == 'upload':
                    print('   --> upload results')
                    break

                if l == 'fst':
                    if op == 'ft_era_corr':
                        print('   --> feature_era_corr')
                        continue
                    if op == 'set_data':
                        if stra == STRAT_CLUSTER:
                            print('   --> clustering')
                        print('   --> split_data_clusters')
                        continue

                elif l == 'snd':
                    if op == 'set_data':
                        print('   --> snd_layer_training_data')
                        continue
                    elif op == 'train':
                        print('   --> generate_models')
                        continue


def main_l_0(strategies, operations_q, argv, arg_parser):

    arg_parser.add_argument("cluster",
                            help="<cluster> used",
                            nargs=1,
                            default=None)

    args = arg_parser.parse_args(args=argv[1:])

    cl = args.cluster[0]

    start_time = time.time()

    while 0 < len(operations_q):
        op = operations_q.popleft()
        print("op: ", op)

        if op == 'h5':
            set_h5_stores()
            continue

        for stra in strategies:
            strat_dir = STRA_DIRNAME_DICT[stra]

            if op == 'train':
                generate_cl_model(strat_dir, cl)
                continue

            if op == 'proba':
                cluster_proba(strat_dir, stra, cl)
                continue

    print("--- %s seconds ---" % (time.time() - start_time))


def main(argv):
    """Program entry point.
    :param argv: command-line arguments
    :type argv: :class:`list`
    """

    arg_parser = argparse.ArgumentParser(
        prog=argv[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument("layer",
                            help="<layer> used",
                            nargs=1,
                            default=['fst'])
    # ['fst', 'snd', 'full']
    arg_parser.add_argument("strat",
                            help="<strat> used",
                            nargs=1,
                            default=[STRAT_CLUSTER])
    # [STRAT_ERA_GRAPH, STRAT_CLUSTER, 'full']
    arg_parser.add_argument("operations",
                            help="<operation> to realize",
                            nargs='+',
                            default=['prediction'])

    args = arg_parser.parse_args(args=argv[1:])
    layers = ['fst', 'snd'] if args.layer[0] == 'full' else args.layer
    strategies = args.strat
    operations_q = deque([
        op for op in ALL_OPERATIONS for arg_op in args.operations
        if arg_op == op
    ])

    if '0' in layers:
        idx_0 = layers.index('0')
        layers.pop(idx_0)
        main_l_0(strategies, operations_q, argv, arg_parser)

    if len(layers) == 0:
        return 0

    print("layers: ", layers)
    print("strategies: ", strategies)
    print("operations: ", operations_q)

    print_funct_calls(layers, strategies, operations_q)

    start_time = time.time()

    while 0 < len(operations_q):
        op = operations_q.popleft()
        print("op: ", op)

        if op == 'h5':
            set_h5_stores()
            continue

        for stra in strategies:
            print("strat: ", stra)
            strat_dir = STRA_DIRNAME_DICT[stra]
            if op == 'ft_sel':
                print('   --> ft_sel')
                ft_selection(strat_dir)
                continue

            if op == 'mut_i':
                print('   --> ft_sel')
                eras_mut_info(strat_dir)
                continue

            if stra == STRAT_CLUSTER and op == 'ft_era_corr':
                feature_era_corr(TRAINING_DATA_FP, TRAINING_STORE_H5_FP)
                continue

            for l in layers:
                print("layer: ", l)

                if op == 'train':
                    generate_models(strat_dir, stra, l)
                    continue
                if op == 'upload':
                    upload_results(strat_dir, l)
                    break
                if op == 'prediction':
                    make_prediction(strat_dir, stra, l)
                    continue

                if l == 'fst':
                    if op == 'proba':
                        cluster_proba(strat_dir, stra)
                        continue
                    if op == 'set_data':
                        if stra == STRAT_CLUSTER:
                            clustering(strat_dir)
                        elif stra == STRAT_CLUSTER_2:
                            clustering_2(strat_dir)
                        elif stra == STRAT_ERA_SIMPLE:
                            simple_era_clustering(strat_dir)
                        split_data_clusters(strat_dir)
                        continue

                elif l == 'snd':
                    if op == 'set_data':
                        snd_layer_training_data(stra)
                        continue

    print("--- %s seconds ---" % (time.time() - start_time))

    # while 0 < len(operations_q):
    #     op = operations_q.popleft()
    #     if op == 'upload':

    return 0


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    entry_point()
