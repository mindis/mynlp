
from dbmanager import SqlManager

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict


def normalize(arr_x, eps=1e-6, M=None):
    if M is None:
        return (arr_x - np.mean(arr_x, axis=0)) / (np.std(arr_x, axis=0) + eps)
    else:
        # return (arr_x - np.mean(arr_x, axis=0)) / (np.std(arr_x, axis=0) + eps)
        return (arr_x - np.mean(arr_x[:M], axis=0)) / (np.std(arr_x[:M], axis=0) + eps)


def dict_to_list(dict, key_list=None):
    arr = list()
    ordered_key_list = list()

    if key_list is None:
        key_list = list(dict.keys())

    for key in dict.keys():
        if key in key_list:
            ordered_key_list.append(key)
            arr.append(dict[key])

    return np.stack(arr, axis=-1), ordered_key_list


def predict_plot(model, dataset, columns_list, size=250, save_dir='out.png'):

    cost_rate = 0.000
    idx_y = columns_list.index('log_y')
    idx_pos = columns_list.index('positive')

    true_y = np.zeros(size)
    pred_both = np.zeros_like(true_y)
    pred_pos = np.zeros_like(true_y)
    pred_y = np.zeros_like(true_y)
    pred_avg = np.zeros_like(true_y)

    pred_chart = np.zeros_like(true_y)
    pred_pos_val = np.zeros_like(true_y)
    pred_y_val = np.zeros_like(true_y)
    real_pos_val = np.zeros_like(true_y)
    real_y_val = np.zeros_like(true_y)

    prev_w_both = 0
    prev_w_pos = 0
    prev_w_y = 0
    for j, (features, labels) in enumerate(dataset.take(size)):
        predictions = model.predict(features)
        true_y[j] = labels[0, 0, idx_y]
        pred_chart[j] = predictions[0, 0, idx_y]
        pred_pos_val[j] = predictions[0, 0, idx_pos]
        pred_y_val[j] = predictions[0, 0, idx_y]
        real_pos_val[j] = labels[0, 0, idx_pos]
        real_y_val[j] = labels[0, 0, idx_y]

        if predictions[0, 0, idx_y] > 0:
            pred_y[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_y)
            prev_w_y = 1
        else:
            pred_y[j] = - cost_rate * prev_w_y
            prev_w_y = 0
        if predictions[0, 0, idx_pos] > 0:
            pred_pos[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_pos)
            prev_w_pos = 1
        else:
            pred_pos[j] = - cost_rate * prev_w_pos
            prev_w_pos = 0
        if (predictions[0, 0, idx_y] > 0) and (predictions[0, 0, idx_pos] > 0):
            pred_both[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_both)
            prev_w_both = 1
        else:
            pred_both[j] = - cost_rate * prev_w_both
            prev_w_both = 0

        pred_avg[j] = (pred_y[j] + pred_pos[j]) / 2.

    data = pd.DataFrame({'true_y': np.cumsum(np.log(1. + true_y[:(j+1)])),
                         'pred_both': np.cumsum(np.log(1. + pred_both[:(j+1)])),
                         'pred_pos': np.cumsum(np.log(1. + pred_pos[:(j+1)])),
                         'pred_y': np.cumsum(np.log(1. + pred_y[:(j+1)])),
                         'pred_avg': np.cumsum(np.log(1. + pred_avg[:(j+1)])),
                         # 'pred_chart': np.cumsum(np.log(1. + pred_chart)),
    })

    pos_acc = np.sum((pred_pos_val[:(j+1)] > 0) == (real_pos_val[:(j+1)] > 0)) / (j+1)
    pos_recall_p = np.sum((pred_pos_val[:(j+1)] > 0) & (real_pos_val[:(j+1)] > 0)) / np.sum(real_pos_val[:(j+1)] > 0)
    pos_precision_p = np.sum((pred_pos_val[:(j+1)] > 0) & (real_pos_val[:(j+1)] > 0)) / np.sum(pred_pos_val[:(j + 1)] > 0)
    pos_recall_n = np.sum((pred_pos_val[:(j+1)] < 0) & (real_pos_val[:(j+1)] < 0)) / np.sum(real_pos_val[:(j+1)] < 0)
    pos_precision_n = np.sum((pred_pos_val[:(j+1)] < 0) & (real_pos_val[:(j+1)] < 0)) / np.sum(pred_pos_val[:(j + 1)] < 0)

    y_acc = np.sum((pred_y_val[:(j+1)] > 0) == (real_y_val[:(j+1)] > 0)) / (j+1)
    y_recall_p = np.sum((pred_y_val[:(j+1)] > 0) & (real_y_val[:(j+1)] > 0)) / np.sum(real_y_val[:(j+1)] > 0)
    y_precision_p = np.sum((pred_y_val[:(j+1)] > 0) & (real_y_val[:(j+1)] > 0)) / np.sum(pred_y_val[:(j + 1)] > 0)
    y_recall_n = np.sum((pred_y_val[:(j+1)] < 0) & (real_y_val[:(j+1)] < 0)) / np.sum(real_y_val[:(j+1)] < 0)
    y_precision_n = np.sum((pred_y_val[:(j+1)] < 0) & (real_y_val[:(j+1)] < 0)) / np.sum(pred_y_val[:(j + 1)] < 0)

    print("n_pos: {} / n_neg: {}".format(np.sum(true_y > 0), np.sum(true_y < 0)))
    print("[[positive]] acc: {:.4f} / [recall] p: {:.4f}, n: {:.4f} / [precision] p: {:.4f}, n: {:.4f}".format(pos_acc,
                                                                                           pos_recall_p, pos_recall_n,
                                                                                           pos_precision_p, pos_precision_n))

    print("[[return]] acc: {:.4f} / [recall] p: {:.4f}, n: {:.4f} / [precision] p: {:.4f}, n: {:.4f}".format(y_acc,
                                                                                           y_recall_p, y_recall_n,
                                                                                           y_precision_p, y_precision_n))

    # plt.plot(data['true_y'], label='real')
    # plt.plot(data['pred_chart'], label='pred')
    # plt.plot(data['pred_y'], label='pred_y')
    # plt.legend()

    fig = plt.figure()
    plt.plot(data)
    plt.legend(data.columns)
    fig.savefig(save_dir)
    plt.close(fig)

    #
    # for j, (features, labels) in enumerate(dataset.take(size)):
    #     predictions = model.predict(features)
    #     true_y[j] = labels[0, 0, columns_list.index('log_cum_y')]
    #     pred_chart[j] = predictions[0, 0, columns_list.index('log_cum_y')]
    #
    # plt.plot(true_y, label='real')
    # plt.plot(pred_chart, label='pred')
    # plt.legend()



def predict_plot_mtl_cross_section_test(model, dataset_list, save_dir='out.png', ylog=False, eval_type='pos'):
    if dataset_list is False:
        return False
    else:
        input_enc_list, output_dec_list, target_dec_list, features_list, additional_infos, start_date, end_date = dataset_list

    idx_y = features_list.index('log_y')

    true_y = np.zeros(len(input_enc_list) + 1)
    pred_ls = np.zeros_like(true_y)

    pred_q1 = np.zeros_like(true_y)
    pred_q2 = np.zeros_like(true_y)
    pred_q3 = np.zeros_like(true_y)
    pred_q4 = np.zeros_like(true_y)
    pred_q5 = np.zeros_like(true_y)

    # df_infos = pd.DataFrame(columns={'start_d', 'base_d', 'infocode', 'score'})
    for i, (input_enc_t, output_dec_t, target_dec_t) in enumerate(zip(input_enc_list, output_dec_list, target_dec_list)):
        t = i + 1
        assert np.sum(input_enc_t[:, -1, :] - output_dec_t[:, 0, :]) == 0
        new_output_t = np.zeros_like(output_dec_t)
        new_output_t[:, 0, :] = output_dec_t[:, 0, :]

        features = {'input': input_enc_t, 'output': new_output_t}
        labels = target_dec_t

        predictions = model.predict_mtl(features)
        # p_ret, p_pos, p_vol, p_mdd = predictions

        true_y[t] = np.mean(labels[:, 0, idx_y])
        # additional_infos[i]['score'] = predictions['pos'][:, 0, 0]
        # df_infos = pd.concat([df_infos, pd.DataFrame({'start_d': start_date,
        #                                    'base_d': additional_infos[i]['date'],
        #                                    'infocode': additional_infos[i]['assets_list'],
        #                                    'score': predictions['pos'][:, 0, 0]})], ignore_index=True)
        if eval_type == 'pos':
            value_ = predictions['pos'][:, 0, 0]
        elif eval_type == 'pos20':
            value_ = predictions['pos20'][:, 0, 0]
        elif eval_type == 'ret':
            value_ = predictions['ret'][:, 0, 0]
        elif eval_type == 'ir20':
            value_ = predictions['ret'][:, 0, 1] / np.abs(predictions['std'][:, 0, 0])
        elif eval_type == 'ir60':
            value_ = predictions['ret'][:, 0, 2] / np.abs(predictions['std'][:, 0, 1])
        elif eval_type == 'ir120':
            value_ = predictions['ret'][:, 0, 3] / np.abs(predictions['std'][:, 0, 2])

        q1_crit, q2_crit, q3_crit, q4_crit = np.percentile(value_, q=[80, 60, 40, 20])
        pred_q1[t] = np.mean(labels[value_ >= q1_crit, 0, idx_y])
        pred_q2[t] = np.mean(labels[(value_ >= q2_crit) & (value_ < q1_crit), 0, idx_y])
        pred_q3[t] = np.mean(labels[(value_ >= q3_crit) & (value_ < q2_crit), 0, idx_y])
        pred_q4[t] = np.mean(labels[(value_ >= q4_crit) & (value_ < q3_crit), 0, idx_y])
        pred_q5[t] = np.mean(labels[(value_ < q4_crit), 0, idx_y])

    # # db insert
    # sqlm = SqlManager()
    # sqlm.db_insert(df_infos[['start_d', 'base_d', 'infocode', 'score']], 'kr_weekly_score_temp', fast_executemany=True)

    data = pd.DataFrame({'true_y': np.cumprod(1. + true_y),
                         'pred_ls': np.cumprod(1. + pred_q1 - pred_q5),
                         'pred_q1': np.cumprod(1. + pred_q1),
                         'pred_q2': np.cumprod(1. + pred_q2),
                         'pred_q3': np.cumprod(1. + pred_q3),
                         'pred_q4': np.cumprod(1. + pred_q4),
                         'pred_q5': np.cumprod(1. + pred_q5)
    })

    fig = plt.figure()
    fig.suptitle('{} ~ {}'.format(start_date, end_date))
    ax1, ax2 = fig.subplots(2, 1)
    ax1.plot(data[['true_y', 'pred_ls', 'pred_q1', 'pred_q5']])
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax1.legend(['true_y', 'long-short', 'long', 'short'], loc='center left', bbox_to_anchor=(1, 0.5))
    if ylog:
        ax1.set_yscale('log', basey=2)

    ax2.plot(data[['true_y', 'pred_q1', 'pred_q2', 'pred_q3', 'pred_q4', 'pred_q5']])
    box = ax2.get_position()
    ax2.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax2.legend(['true_y', 'q1', 'q2', 'q3', 'q4', 'q5'], loc='center left', bbox_to_anchor=(1, 0.5))
    ax2.set_yscale('log', basey=2)

    fig.savefig(save_dir)
    print("figure saved. (dir: {})".format(save_dir))
    plt.close(fig)


def predict_plot_mtl_test(model, dataset_list, save_dir='out.png', ylog=False, eval_type='pos'):
    if dataset_list is False:
        return False
    else:
        input_enc_list, output_dec_list, target_dec_list, features_list, start_date, end_date = dataset_list

    idx_y = features_list.index('log_y')

    true_y = np.zeros(len(input_enc_list) + 1)
    pred_pos_ls = np.zeros_like(true_y)
    pred_pos_ls_wgt_adj = np.zeros_like(true_y)

    pred_pos_l = np.zeros_like(true_y)
    pred_pos_s = np.zeros_like(true_y)

    pred_pos_l_wgt = np.zeros_like(true_y)
    pred_pos_l_wgt_adj = np.zeros_like(true_y)
    pred_pos_s_wgt = np.zeros_like(true_y)
    pred_pos_s_wgt_adj = np.zeros_like(true_y)

    pred_q1 = np.zeros_like(true_y)
    pred_q2 = np.zeros_like(true_y)
    pred_q3 = np.zeros_like(true_y)
    pred_q4 = np.zeros_like(true_y)
    pred_q5 = np.zeros_like(true_y)

    for i, (input_enc_t, output_dec_t, target_dec_t) in enumerate(zip(input_enc_list, output_dec_list, target_dec_list)):
        t = i + 1
        assert np.sum(input_enc_t[:, -1, :] - output_dec_t[:, 0, :]) == 0
        new_output_t = np.zeros_like(output_dec_t)
        new_output_t[:, 0, :] = output_dec_t[:, 0, :]

        features = {'input': input_enc_t, 'output': new_output_t}
        labels = target_dec_t

        predictions = model.predict_mtl(features)
        # p_ret, p_pos, p_vol, p_mdd = predictions

        true_y[t] = np.mean(labels[:, 0, idx_y])

        if eval_type == 'pos':
            crit = 0.5
            value_ = predictions['pos'][:, 0, 0]
        elif eval_type == 'ret':
            crit = 0
            value_ = predictions['ret'][:, 0, 0]
        elif eval_type == 'ir':
            crit = 0
            value_ = predictions['ret'][:, 0, 1] / np.abs(predictions['std'][:, 0, 0])


        n_assets = len(value_)
        is_pos_position = value_ > crit
        is_neg_position = value_ < crit

        q1_crit, q2_crit, q3_crit, q4_crit = np.percentile(value_, q=[80, 60, 40, 20])
        pred_q1[t] = np.mean(labels[value_ >= q1_crit, 0, idx_y])
        pred_q2[t] = np.mean(labels[(value_ >= q2_crit) & (value_ < q1_crit), 0, idx_y])
        pred_q3[t] = np.mean(labels[(value_ >= q3_crit) & (value_ < q2_crit), 0, idx_y])
        pred_q4[t] = np.mean(labels[(value_ >= q4_crit) & (value_ < q3_crit), 0, idx_y])
        pred_q5[t] = np.mean(labels[value_ < q4_crit, 0, idx_y])

        # if predictions['ret'][0, 0, 0] > 0:
        if np.sum(is_pos_position) > 0:
            pred_pos_l[t] = np.mean(labels[is_pos_position, 0, idx_y])
            pred_pos_l_wgt[t] = np.sum(is_pos_position) / n_assets
            pred_pos_l_wgt_adj[t] = np.sum(labels[is_pos_position, 0, idx_y]) / n_assets
        else:
            pred_pos_l[t] = 0
            pred_pos_l_wgt[t] = 0
            pred_pos_l_wgt_adj[t] = 0

        if np.sum(is_neg_position) > 0:
            pred_pos_s[t] = np.mean(labels[is_neg_position, 0, idx_y])
            pred_pos_s_wgt[t] = np.sum(is_neg_position) / n_assets
            pred_pos_s_wgt_adj[t] = np.sum(labels[is_neg_position, 0, idx_y]) / n_assets
        else:
            pred_pos_s[t] = 0
            pred_pos_s_wgt[t] = 0
            pred_pos_s_wgt_adj[t] = 0

        pred_pos_ls[t] = pred_pos_l[t] - pred_pos_s[t]
        pred_pos_ls_wgt_adj[t] = pred_pos_l_wgt_adj[t] - pred_pos_s_wgt_adj[t]


    data = pd.DataFrame({'true_y': np.cumprod(1. + true_y),
                         'pred_pos_ls': np.cumprod(1. + pred_pos_ls),
                         'pred_pos_ls_wgt_adj': np.cumprod(1. + pred_pos_ls_wgt_adj),
                         'pred_pos_l': np.cumprod(1. + pred_pos_l),
                         'pred_pos_s': np.cumprod(1. + pred_pos_s),
                         'pred_pos_l_wgt': pred_pos_l_wgt,
                         'pred_pos_l_wgt_adj': np.cumprod(1. + pred_pos_l_wgt_adj),
                         'pred_pos_s_wgt': pred_pos_s_wgt,
                         'pred_pos_s_wgt_adj': np.cumprod(1. + pred_pos_s_wgt_adj),
                         'pred_q1': np.cumprod(1. + pred_q1),
                         'pred_q2': np.cumprod(1. + pred_q2),
                         'pred_q3': np.cumprod(1. + pred_q3),
                         'pred_q4': np.cumprod(1. + pred_q4),
                         'pred_q5': np.cumprod(1. + pred_q5)
    })

    fig = plt.figure()
    fig.suptitle('{} ~ {}'.format(start_date, end_date))
    ax1, ax2, ax3, ax4 = fig.subplots(4, 1)
    ax1.plot(data[['true_y', 'pred_pos_ls', 'pred_pos_l', 'pred_pos_s']])
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax1.legend(['true_y', 'long-short', 'long', 'short'], loc='center left', bbox_to_anchor=(1, 0.5))
    if ylog:
        ax1.set_yscale('log', basey=2)

    ax2.plot(data[['true_y', 'pred_pos_ls_wgt_adj', 'pred_pos_l_wgt_adj', 'pred_pos_s_wgt_adj']])
    box = ax2.get_position()
    ax2.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax2.legend(['true_y', 'long-short(adj)', 'long(adj)', 'short(adj)'], loc='center left', bbox_to_anchor=(1, 0.5))
    if ylog:
        ax2.set_yscale('log', basey=2)

    ax3.plot(data[['true_y', 'pred_q1', 'pred_q2', 'pred_q3', 'pred_q4', 'pred_q5']])
    box = ax3.get_position()
    ax3.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax3.legend(['true_y', 'q1', 'q2', 'q3', 'q4', 'q5'], loc='center left', bbox_to_anchor=(1, 0.5))
    # if ylog:
    ax3.set_yscale('log', basey=2)

    ax4.plot(data[['pred_pos_l_wgt']])
    box = ax4.get_position()
    ax4.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax4.legend(['long_wgt'], loc='center left', bbox_to_anchor=(1, 0.5))
    ax4.set_ylim([0., 1.])

    fig.savefig(save_dir)
    print("figure saved. (dir: {})".format(save_dir))
    plt.close(fig)


def predict_plot_mtl(model, dataset, columns_list, size=250, save_dir='out.png'):

    cost_rate = 0.000
    idx_y = columns_list.index('log_y')
    idx_pos = columns_list.index('positive')

    true_y = np.zeros(size)
    pred_both = np.zeros_like(true_y)
    pred_pos = np.zeros_like(true_y)
    pred_y = np.zeros_like(true_y)
    pred_avg = np.zeros_like(true_y)

    pred_chart = np.zeros_like(true_y)
    pred_pos_val = np.zeros_like(true_y)
    pred_y_val = np.zeros_like(true_y)
    real_pos_val = np.zeros_like(true_y)
    real_y_val = np.zeros_like(true_y)

    prev_w_both = 0
    prev_w_pos = 0
    prev_w_y = 0
    for j, (features, labels) in enumerate(dataset.take(size)):
        predictions = model.predict_mtl(features)
        # p_ret, p_pos, p_vol, p_mdd = predictions

        true_y[j] = labels[0, 0, idx_y]
        pred_chart[j] = predictions['ret'][0, 0, 0]
        pred_pos_val[j] = predictions['pos'][0, 0, 0] - 0.5
        pred_y_val[j] = predictions['ret'][0, 0, 0]
        real_pos_val[j] = labels[0, 0, idx_pos]
        real_y_val[j] = labels[0, 0, idx_y]

        if predictions['ret'][0, 0, 0] > 0:
            pred_y[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_y)
            prev_w_y = 1
        else:
            pred_y[j] = - cost_rate * prev_w_y
            prev_w_y = 0
        if predictions['pos'][0, 0, 0] > 0.5:
            pred_pos[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_pos)
            prev_w_pos = 1
        else:
            pred_pos[j] = - cost_rate * prev_w_pos
            prev_w_pos = 0
        if (predictions['ret'][0, 0, 0] > 0) and (predictions['pos'][0, 0, 0] > 0.5):
            pred_both[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_both)
            prev_w_both = 1
        else:
            pred_both[j] = - cost_rate * prev_w_both
            prev_w_both = 0

        pred_avg[j] = (pred_y[j] + pred_pos[j]) / 2.

    data = pd.DataFrame({'true_y': np.cumsum(np.log(1. + true_y[:(j+1)])),
                         'pred_both': np.cumsum(np.log(1. + pred_both[:(j+1)])),
                         'pred_pos': np.cumsum(np.log(1. + pred_pos[:(j+1)])),
                         'pred_y': np.cumsum(np.log(1. + pred_y[:(j+1)])),
                         'pred_avg': np.cumsum(np.log(1. + pred_avg[:(j+1)])),
                         # 'pred_chart': np.cumsum(np.log(1. + pred_chart)),
    })

    pos_acc = np.sum((pred_pos_val[:(j+1)] > 0) == (real_pos_val[:(j+1)] > 0)) / (j+1)
    pos_recall_p = np.sum((pred_pos_val[:(j+1)] > 0) & (real_pos_val[:(j+1)] > 0)) / np.sum(real_pos_val[:(j+1)] > 0)
    pos_precision_p = np.sum((pred_pos_val[:(j+1)] > 0) & (real_pos_val[:(j+1)] > 0)) / np.sum(pred_pos_val[:(j + 1)] > 0)
    pos_recall_n = np.sum((pred_pos_val[:(j+1)] < 0) & (real_pos_val[:(j+1)] < 0)) / np.sum(real_pos_val[:(j+1)] < 0)
    pos_precision_n = np.sum((pred_pos_val[:(j+1)] < 0) & (real_pos_val[:(j+1)] < 0)) / np.sum(pred_pos_val[:(j + 1)] < 0)

    y_acc = np.sum((pred_y_val[:(j+1)] > 0) == (real_y_val[:(j+1)] > 0)) / (j+1)
    y_recall_p = np.sum((pred_y_val[:(j+1)] > 0) & (real_y_val[:(j+1)] > 0)) / np.sum(real_y_val[:(j+1)] > 0)
    y_precision_p = np.sum((pred_y_val[:(j+1)] > 0) & (real_y_val[:(j+1)] > 0)) / np.sum(pred_y_val[:(j + 1)] > 0)
    y_recall_n = np.sum((pred_y_val[:(j+1)] < 0) & (real_y_val[:(j+1)] < 0)) / np.sum(real_y_val[:(j+1)] < 0)
    y_precision_n = np.sum((pred_y_val[:(j+1)] < 0) & (real_y_val[:(j+1)] < 0)) / np.sum(pred_y_val[:(j + 1)] < 0)

    print("n_pos: {} / n_neg: {}".format(np.sum(true_y > 0), np.sum(true_y < 0)))
    print("[[positive]] acc: {:.4f} / [recall] p: {:.4f}, n: {:.4f} / [precision] p: {:.4f}, n: {:.4f}".format(pos_acc,
                                                                                           pos_recall_p, pos_recall_n,
                                                                                           pos_precision_p, pos_precision_n))

    print("[[return]] acc: {:.4f} / [recall] p: {:.4f}, n: {:.4f} / [precision] p: {:.4f}, n: {:.4f}".format(y_acc,
                                                                                           y_recall_p, y_recall_n,
                                                                                           y_precision_p, y_precision_n))

    fig = plt.figure()
    plt.plot(data)
    plt.legend(data.columns)
    fig.savefig(save_dir)
    print("figure saved. (dir: {})".format(save_dir))
    plt.close(fig)



def predict_plot_with_actor(model, actor, dataset, columns_list, size=250, save_dir='out.png'):

    cost_rate = 0.000
    idx_y = columns_list.index('log_y')
    idx_pos = columns_list.index('positive')
    idx_ma20 = columns_list.index('y_20d')

    true_y = np.zeros(size)
    pred_both = np.zeros_like(true_y)
    pred_pos = np.zeros_like(true_y)
    pred_y = np.zeros_like(true_y)
    pred_avg = np.zeros_like(true_y)
    pred_actor = np.zeros_like(true_y)
    action_arr = np.zeros_like(true_y)

    prev_w_both = 0
    prev_w_pos = 0
    prev_w_y = 0
    for j, (features, labels) in enumerate(dataset.take(size)):
        predictions = model.predict(features)
        actions, v = actor.evaluate_state(predictions, stochastic=False)
        a_value = actions.numpy()[0, 0]
        assert (a_value >= 0) and (a_value <= 1)
        true_y[j] = labels[0, 0, idx_y]
        pred_actor[j] = labels[0, 0, idx_y] * a_value
        action_arr[j] = a_value

        if predictions[0, 0, idx_y] > 0:
            pred_y[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_y)
            prev_w_y = 1
        else:
            pred_y[j] = - cost_rate * prev_w_y
            prev_w_y = 0
        if predictions[0, 0, idx_pos] > 0:
            pred_pos[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_pos)
            prev_w_pos = 1
        else:
            pred_pos[j] = - cost_rate * prev_w_pos
            prev_w_pos = 0
        if (predictions[0, 0, idx_y] > 0) and (predictions[0, 0, idx_pos] > 0):
            pred_both[j] = labels[0, 0, idx_y] - cost_rate * (1. - prev_w_both)
            prev_w_both = 1
        else:
            pred_both[j] = - cost_rate * prev_w_both
            prev_w_both = 0

        pred_avg[j] = (pred_y[j] + pred_pos[j]) / 2.

    data = pd.DataFrame({'true_y': np.cumsum(np.log(1. + true_y)),
                         'pred_both': np.cumsum(np.log(1. + pred_both)),
                         'pred_pos': np.cumsum(np.log(1. + pred_pos)),
                         'pred_y': np.cumsum(np.log(1. + pred_y)),
                         'pred_avg': np.cumsum(np.log(1. + pred_avg)),
                         'pred_actor': np.cumsum(np.log(1. + pred_actor)),
    })

    # plt.plot(data['true_y'], label='real')
    # plt.plot(data['pred_chart'], label='pred')
    # plt.plot(data['pred_y'], label='pred_y')
    # plt.legend()

    fig = plt.figure()
    ax1, ax2 = fig.subplots(2, 1)
    ax1.plot(data)
    ax1.legend(data.columns)
    ax2.plot(np.arange(action_arr), action_arr)
    ax2.set_ylim([0., 1.])
    fig.savefig(save_dir)
    plt.close(fig)

    #
    # for j, (features, labels) in enumerate(dataset.take(size)):
    #     predictions = model.predict(features)
    #     true_y[j] = labels[0, 0, columns_list.index('log_cum_y')]
    #     pred_chart[j] = predictions[0, 0, columns_list.index('log_cum_y')]
    #
    # plt.plot(true_y, label='real')
    # plt.plot(pred_chart, label='pred')
    # plt.legend()


class FeatureCalculator:
    # example:
    #
    def __init__(self, prc, sampling_freq):
        self.sampling_freq = sampling_freq
        self.log_cum_y = np.log(prc / prc[0, :])
        self.y_1d = self.get_y_1d()
        self.log_y = self.moving_average(sampling_freq, sampling_freq=sampling_freq)

    def get_y_1d(self, eps=1e-6):
        return np.concatenate([self.log_cum_y[0:1, :], np.exp(self.log_cum_y[1:, :] - self.log_cum_y[:-1, :] + eps) - 1.], axis=0)

    def moving_average(self, n, sampling_freq=1):
        return np.concatenate([self.log_cum_y[:n, :], self.log_cum_y[n:, :] - self.log_cum_y[:-n, :]], axis=0)[::sampling_freq, :]

    def positive(self):
        return (self.log_y >= 0) * np.array(1., dtype=np.float32) - (self.log_y < 0) * np.array(1., dtype=np.float32)

    def get_std(self, n, sampling_freq=1):
        stdarr = np.zeros_like(self.y_1d)
        for t in range(1, len(self.y_1d)):
            stdarr[t, :] = np.std(self.y_1d[max(0, t - n):(t + 1), :], axis=0)
        return stdarr[::sampling_freq, :]

    def get_mdd(self, n, sampling_freq=1):
        mddarr = np.zeros_like(self.log_cum_y)
        for t in range(len(self.log_cum_y)):
            mddarr[t, :] = self.log_cum_y[t, :] - np.max(self.log_cum_y[max(0, t - n):(t + 1), :])

        return mddarr[::sampling_freq, :]

    def generate_features(self):
        features = OrderedDict()
        features['log_y'] = self.log_y
        features['log_cum_y'] = self.log_cum_y[::self.sampling_freq]
        features['positive'] = self.positive()
        for n in [20, 60, 120]:
            features['y_{}d'.format(n)] = self.moving_average(n, self.sampling_freq)
            features['std{}d'.format(n)] = self.get_std(n, self.sampling_freq)
            features['mdd{}d'.format(n)] = self.get_mdd(n, self.sampling_freq)

        # remove redundant values at t=0 (y=0, cum_y=0, ...)
        for key in features.keys():
            features[key] = features[key][1:]

        return features


def getWeights(d, size):
    w=[1.]
    for k in range(1, size):
        w_ = -w[-1] / k * (d-k+1)
        w.append(w_)
    w = np.array(w[::-1]).reshape(-1, 1)
    return w

def plotWeights(dRange, nPlots, size):
    w = pd.DataFrame()
    for d in np.linspace(dRange[0], dRange[1], nPlots):
        w_ = getWeights(d, size=size)
        w_ = pd.DataFrame(w_, index=range(w_.shape[0])[::1], columns=[d])
        w = w.join(w_, how='outer')
    ax = w.plot()
    ax.legend(loc='upper left'); mpl.show()
    return

def fracDiff(series, d, thres=.01):
    w = getWeights(d, series.shape[0])
    w_ = np.cumsum(abs(w))
    w_ /= w_[-1]
    skip = w_[w_>thres].shape[0]
    df = {}
    for name in series.columns:
        seriesF, df_ = series[[name]].fillna(method='ffill').dropna(), pd.Series()
        for iloc in range(skip, seriesF.shape[0]):
            loc= seriesF.index[iloc]
            if not np.isfinite(series.loc[loc, name]):
                continue
            df_[loc] = np.dot(w[-(iloc+1):, :].T, seriesF.loc[:loc])[0, 0]
        df[name] = df_.copy(deep=True)
    df = pd.concat(df, axis=1)
    return df

def fracDiff_FFD(series, d, thres=1e-5):
    # w = getWeights_FFD(d, thres)
    w = getWeights(d, thres)
    width = len(w) - 1
    df = {}
    for name in series.columns:
        seriesF, df_ = series[[name]].fillna(method='ffill').dropna(), pd.Series()
        for iloc1 in range(width, seriesF.shape[0]):
            loc0, loc1 = seriesF.index[iloc1 - width], seriesF.index[iloc1]
            if not np.isinfinite(series.loc[loc1, name]):
                continue
            df_[loc1] = np.dot(w.T, seriesF.loc[loc0:loc1])[0, 0]
        df[name] = df_.copy(deep=True)
    df = pd.concat(df, axis=1)
    return df


import matplotlib.pyplot as plt
# dataset = ds.data_generator.df_pivoted[['spx index']]
# dataset.columns = ['price']


def get_technical_indicators(dataset):
    # Create 7 and 21 days Moving Average
    dataset['ma7'] = dataset['price'].rolling(window=7).mean()
    dataset['ma21'] = dataset['price'].rolling(window=21).mean()

    # Create MACD
    dataset['26ema'] = dataset['price'].ewm(span=26).mean()
    dataset['12ema'] = dataset['price'].ewm(span=12).mean()
    dataset['MACD'] = (dataset['12ema'] - dataset['26ema'])

    # Create Bollinger Bands
    dataset['20sd'] = dataset['price'].rolling(20).std(ddof=1)
    dataset['upper_band'] = dataset['ma21'] + (dataset['20sd'] * 2)
    dataset['lower_band'] = dataset['ma21'] - (dataset['20sd'] * 2)

    # Create Exponential moving average
    dataset['ema'] = dataset['price'].ewm(com=0.5).mean()

    # Create Momentum
    dataset['momentum'] = dataset['price'] - 1

    return dataset


def get_fft(dataset):
    assert len(dataset.columns) == 1
    dataset_log = np.log(dataset)
    dataset_log.reset_index(drop=True, inplace=True)
    close_fft = np.fft.fft(np.squeeze(np.array(dataset_log)))
    fft_df = pd.DataFrame({'fft': close_fft})
    fft_df['absolute'] = fft_df['fft'].apply(lambda x: np.abs(x))
    fft_df['angle'] = fft_df['fft'].apply(lambda x: np.angle(x))

    plt.figure(figsize=(14, 7), dpi=100)
    fft_list = np.asarray(fft_df['fft'].tolist())
    for num_ in [3, 6, 9, 100]:
        fft_list_m10 = np.copy(fft_list)
        fft_list_m10[num_:-num_] = 0
        plt.plot(np.fft.ifft(fft_list_m10), label='Fourier transform with {} components'.format(num_))
    plt.plot(dataset_log,  label='Real')
    plt.xlabel('Days')
    plt.ylabel('USD')
    plt.title('Figure 3: Goldman Sachs (close) stock prices & Fourier transforms')
    plt.legend()
    plt.show()


def plot_technical_indicators(dataset, last_days):
    dataset.reset_index(drop=True, inplace=True)
    plt.figure(figsize=(16, 10), dpi=100)
    shape_0 = dataset.shape[0]
    xmacd_ = shape_0 - last_days

    dataset = dataset.iloc[-last_days:, :]
    dataset.reset_index()
    x_ = range(3, dataset.shape[0])
    x_ = list(dataset.index)

    # Plot first subplot
    plt.subplot(2, 1, 1)
    plt.plot(dataset['ma7'], label='MA 7', color='g', linestyle='--')
    plt.plot(dataset['price'], label='Closing Price', color='b')
    plt.plot(dataset['ma21'], label='MA 21', color='r', linestyle='--')
    plt.plot(dataset['upper_band'], label='Upper Band', color='c')
    plt.plot(dataset['lower_band'], label='Lower Band', color='c')
    plt.fill_between(x_, dataset['lower_band'], dataset['upper_band'], alpha=0.35)
    plt.title('Technical indicators for Goldman Sachs - last {} days.'.format(last_days))
    plt.ylabel('USD')
    plt.legend()

    # Plot second subplot
    plt.subplot(2, 1, 2)
    plt.title('MACD')
    plt.plot(dataset['MACD'], label='MACD', linestyle='-.')
    plt.hlines(15, xmacd_, shape_0, colors='g', linestyles='--')
    plt.hlines(-15, xmacd_, shape_0, colors='g', linestyles='--')
    plt.plot(dataset['momentum'], label='Momentum', color='b', linestyle='-')

    plt.legend()
    plt.show()
