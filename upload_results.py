import os
import sys
import json
import numerapi
import pandas as pd
from reader_csv import ReaderCSV

TOURNAMENT_NAME = "kazutsugi"
TARGET_NAME = "prediction_kazutsugi"


def load_json(filepath):
    with open(filepath, 'r') as f:
        json_data = json.load(f)

        return json_data


def load_data(data_filepath, data_col=None):
    file_reader = ReaderCSV(data_filepath)
    input_data = file_reader.read_csv(
        columns=data_col).set_index('id')

    return input_data


def load_predict_file(pred_fp, model_type):
    predict_data = load_data(pred_fp)
    predict_series = predict_data[model_type]
    predict_df = pd.DataFrame(
        {'id': predict_series.index, TARGET_NAME: predict_series.values}).set_index('id')

    print("predict_df: ", predict_df)

    return predict_df


def load_orig_id_era_dt():
    data_filepath = 'numerai_tournament_data.csv'
    file_reader = ReaderCSV(data_filepath)
    orig_df = file_reader.read_csv(
        columns=['id', 'era', 'data_type']).set_index('id')

    return orig_df


def main():

    orig_data_id_era_dt = load_orig_id_era_dt()

    sub_dirname = 'data_subsets_036'

    pred_suffix = 'snd'  # 'full', 'fst'

    pred_validation_fp = sub_dirname + \
        '/final_predict_validation_' + pred_suffix + '.csv'
    pred_test_fp = sub_dirname + '/final_predict_test_' + pred_suffix + '.csv'
    pred_live_fp = sub_dirname + '/final_predict_live_' + pred_suffix + '.csv'

    model_type = 'rf'

    valid_data = load_predict_file(pred_validation_fp, model_type)
    test_data = load_predict_file(pred_test_fp, model_type)
    live_data = load_predict_file(pred_live_fp, model_type)

    pred_data = pd.concat([valid_data, test_data, live_data], axis=0)
    # pred_data = live_data

    # re-order result ids to match exactly original tournament file
    pred_data = pred_data.reindex(orig_data_id_era_dt.index)

    # tournament_data = load_data(
    #    'numerai_tournament_data.csv', data_col=['id', 'data_type'])
    #tournament_data = tournament_data.loc[tournament_data['data_type'] == 'live']

    # print("pred_data: ", pred_data)
    # print("pred_data.index: ", pred_data.index)
    # print("tournament_data index: ", tournament_data.index)
    # same_idx = pred_data.index == tournament_data.index
    # print("same_idx: ", same_idx)

    prediction_fp = "numerai_prediction.csv"

    with open(prediction_fp, 'w') as fp:
        pred_data.to_csv(fp)

    credentials = load_json('upload_credentials.json')

    print("credentials: ", credentials)

    # provide api tokens
    public_id = 'GVVAJB4FTYC2YKLBY7TINPR4MOZO4PD5'  # credentials['public_id']
    # credentials['secret_key']
    secret_key = 'WOJS5R6CFC2FG2OKPBSOA5S3URH2DO2QH35XAYSLG4LXYL4OSXLNSPFEAZVVHXKM'
    napi = numerapi.NumerAPI(public_id, secret_key)

    # upload predictions
    submission_id = napi.upload_predictions("numerai_prediction.csv")
    # check submission status
    napi.submission_status()


if __name__ == '__main__':
    main()