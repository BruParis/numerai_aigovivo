import os
import sys
import numpy as np
import pandas as pd
import itertools
import sklearn.metrics as sm
from sklearn import preprocessing
from sklearn import utils
from imblearn.over_sampling import SMOTE, ADASYN

from ..common import *
from ..data_analysis import rank_proba, pred_score
from ..models import Model, ModelType, construct_model, get_metrics_filename


class ModelGenerator():
    def _format_input_target(self, data_df):

        data_aux = data_df.copy()

        # if ERA_LABEL in data_aux.columns:
        #     data_aux = data_aux.drop([ERA_LABEL], axis=1)

        input_df = data_aux.drop([TARGET_LABEL], axis=1)
        target_df = data_aux.loc[:, [TARGET_LABEL]]

        # mutiply target value to get target class index
        target_df = TARGET_FACT_NUMERIC * target_df

        return input_df, target_df

    def _oversampling_2(self, train_data):
        print("train_data: ", train_data)
        ft_col = [c for c in train_data.columns if c.startswith('feature_')]
        train_eras = set(train_data.era.values)

        res = pd.DataFrame()
        for era in train_eras:
            era_data = train_data.loc[train_data['era'] == era]
            era_input_data = era_data[ft_col]
            era_target_data = era_data[TARGET_LABEL]

            lab_enc = preprocessing.LabelEncoder()
            encoded = lab_enc.fit_transform(era_target_data)

            # era_osampled, target_resampled_encod = SMOTE().fit_resample(
            #     era_input_data, encoded)
            era_osampled, target_resampled_encod = ADASYN().fit_resample(
                era_input_data, encoded)
            era_target_resampled = lab_enc.inverse_transform(
                target_resampled_encod)

            era_osampled[TARGET_LABEL] = era_target_resampled
            era_osampled['era'] = era
            era_osampled = era_osampled.sample(frac=1).reset_index(drop=True)

            res = pd.concat([res, era_osampled], axis=0)

        res_sampling_dict = {
            t: len(res.loc[res[TARGET_LABEL] == t].index)
            for t in TARGET_VALUES
        }

        print("res: ", res)
        print("res_sampling_dict: ", res_sampling_dict)

        return res

    def _display_cross_tab(self, test_target):

        cross_tab = pd.crosstab(test_target[TARGET_LABEL],
                                test_target['prediction'],
                                rownames=['Actual Target'],
                                colnames=['Predicted Target'])
        cross_tab_perc = cross_tab.apply(
            lambda r: (100 * round(r / r.sum(), 2)).astype(int), axis=1)
        cross_tab['Total'] = cross_tab.sum(axis=1)
        cross_tab = cross_tab.append(cross_tab.sum(), ignore_index=True)

        print("cross_tab: ", cross_tab)
        cross_tab_perc['Total'] = cross_tab['Total']
        cross_tab_perc = cross_tab_perc.append(cross_tab.iloc[-1],
                                               ignore_index=True)
        print("Cross Tab %: ", cross_tab_perc)

    def __init__(self, dir_path):

        self.dir_path = dir_path

        self.model = None
        self.model_params = None
        self.num_metrics = 0

    def start_model_type(self, model_type, model_prefix=None):
        self.model_type = model_type
        self.model_prefix = model_prefix

        self.num_metrics = 0

    def generate_model(self, model_params, debug=False):

        if self.model_type is None:
            print("Error: Model type not provided for generation.")
            return None

        if self.model_type == ModelType.K_NN and self.model_prefix is None:
            print("Error: Model is of type K_NN but no prefix provided.")
            return None

        self.model_params = model_params
        self.model = construct_model(self.dir_path,
                                     self.model_type,
                                     self.model_params,
                                     model_debug=debug)

    def format_train_data(self, train_data):

        balanced_train_data = self._oversampling_2(train_data)

        train_input, train_target = self._format_input_target(
            balanced_train_data)

        return train_input, train_target

    def build_model(self, train_input, train_target, random_search=False):

        if self.model_type == ModelType.RandomForest or self.model_type == ModelType.XGBoost:
            self.model.build_model(train_input, train_target, random_search)
        else:
            self.model.build_model(train_input, train_target)

        model_dict = dict()
        model_dict['type'] = self.model_type.name
        model_dict['prefix'] = self.model_prefix
        model_dict['params'] = self.model_params

        return self.model

    def evaluate_model(self, cl_cols, data_df):

        input_df = data_df[cl_cols]

        data_input, data_target = self._format_input_target(input_df)

        if ERA_LABEL in data_input.columns:
            data_input = data_input.drop([ERA_LABEL], axis=1)

        data_target['prediction'] = self.model.predict(data_input)

        print("pred: ", data_target['prediction'])
        pred_dict = {
            t: len(data_target.loc[data_target['prediction'] == t].index)
            for t in range(0, 5)
        }
        print("pred_dict: ", pred_dict)

        test_proba = self.model.predict_proba(data_input)

        self._display_cross_tab(data_target)

        columns_labels = [
            self.model_type.name + '_' + proba_label
            for proba_label in COL_PROBA_NAMES
        ]
        test_proba_df = pd.DataFrame(test_proba,
                                     data_input.index,
                                     columns=columns_labels)

        print("test_proba_df: ", test_proba_df)

        data_target['proba'] = test_proba.tolist()
        log_loss = sm.log_loss(data_target[TARGET_LABEL], test_proba.tolist())
        accuracy_score = sm.accuracy_score(data_target[TARGET_LABEL],
                                           data_target['prediction'])

        eval_score_dict = dict()

        eval_score_dict['log_loss'] = log_loss
        eval_score_dict['accuracy_score'] = accuracy_score

        eval_rank = rank_proba(test_proba_df, self.model_type.name)
        eval_rank['era'] = data_df['era']

        model_eval_data = pd.concat([test_proba_df, eval_rank], axis=1)
        model_eval_fn = self.model_type.name + '_train_data.csv'
        model_eval_fp = self.dir_path + '/' + model_eval_fn
        with open(model_eval_fp, 'w') as fp:
            eval_score_dict['train_data_fp'] = model_eval_fp
            model_eval_data.to_csv(fp)

        eval_score_dict['eval_score'] = pred_score(eval_rank,
                                                   self.model_type.name,
                                                   data_target[TARGET_LABEL])

        print("eval: ", eval_score_dict)

        if self.model_type is ModelType.NeuralNetwork:
            print("plot history")
            self.model.save_hist_plot(suffix=self.num_metrics)

        return eval_score_dict

    def append_metrics(self, data_eval):

        cols_n = [k for k in self.model_params.keys()
                  ] + ['log_loss', 'accuracy_score', 'corr_mean']
        log_loss = data_eval['log_loss']
        accuracy_score = data_eval['accuracy_score']
        corr_mean = data_eval['eval_score']['corr_mean']
        m_values = [v for v in self.model_params.values()
                    ] + [log_loss, accuracy_score, corr_mean]
        metrics_df = pd.DataFrame(data=[m_values], columns=cols_n)

        metrics_fp = self.dir_path + '/' + get_metrics_filename(
            self.model_type)

        w_header = self.num_metrics == 0
        w_a = 'w' if w_header else 'a'
        with open(metrics_fp, w_a) as f:
            metrics_df.to_csv(f, header=w_header, index=False)

        self.num_metrics += 1
