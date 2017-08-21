"""因子分组函数
分组返回加过 grouping_info : DateFrame(index=[date,IDs],columns=[group_id])
"""

import numpy as np
import pandas as pd

from utils.tool_funcs import parse_industry

def _add_group_id(factor_data,factor_name,n_groups,ascending=True):
    """给因子数据加入组号
    factor_data 格式:【index=IDs】
    """
    factor_data=factor_data.sort_values(factor_name,ascending=ascending).dropna(subset=[factor_name])
    stockNumsPerGroup=int(np.round(len(factor_data)/n_groups))
    while len(factor_data) - stockNumsPerGroup * (n_groups - 1) < 0:
        n_groups -= 1
    stockNumsLastGroup = len(factor_data) - stockNumsPerGroup * (n_groups - 1)
    factor_data['group_id']= np.hstack((
        np.sort(np.tile(np.arange(1, n_groups), stockNumsPerGroup)), np.tile(n_groups, stockNumsLastGroup)))
    return factor_data[['group_id']]

def typical_grouping(factor,data_source, config):
    """典型分组方式:全市场打分
    grouping_info 格式: DataFrame[index=[date,IDs],group_id]
    """
    N = config.total_groups
    is_ascending = True if factor.direction == -1 else False
    data = factor.data
    all_dates = data.index.levels[0]

    group_info_list = []
    for date in all_dates:
        section_factor = data.ix[date]
        group_id = _add_group_id(section_factor, factor.axe, n_groups=N, ascending=is_ascending)
        idx = pd.MultiIndex.from_product([[date],group_id.index])
        group_id.index = idx
        group_info_list.append(group_id)
    grouping_info = pd.concat(group_info_list)
    grouping_info.index.names = ['date','IDs']
    factor.grouping_info['typical'] = grouping_info


def industry_neutral(factor,data_source, config):
    """行业中性化方式
    每一个时间截面按照不同行业进行分层,每一层再进行打分
    """
    N = config.total_groups
    industry_name = config.neutral_industry_used
    industry_axe = parse_industry(industry_name)
    data = factor.data
    is_ascending = True if factor.direction == -1 else False

    all_ids = data.index.levels[1].unique().tolist()
    all_dates = data.index.levels[0].tolist()
    industry_info = data_source.sector.get_stock_industry_info(ids=all_ids,industry=industry_name,
                                                               dates=all_dates)
    common = data.merge(industry_info, left_index=True, right_index=True, how='left')

    group_info_list = []
    for date in all_dates:
        section_factor = common.ix[date]
        group_id = section_factor.groupby(
            industry_axe,group_keys=False).apply(_add_group_id,factor_name=factor.axe,
                                                 n_groups=N,ascending=is_ascending)
        idx = pd.MultiIndex.from_product([[date], group_id.index])
        group_id.index = idx
        group_info_list.append(group_id)
    grouping_info = pd.concat(group_info_list)
    grouping_info.index.names = ['date','IDs']
    factor.grouping_info['industry_neutral'] = grouping_info

def float_mv_neutral(factor,data_source,config):
    """流通市值中性分组
    按照流通市值进行分层,再在层内进行打分
    """

    N = config.total_groups
    data = factor.data
    is_ascending = True if factor.direction == -1 else False
    sub_groups = config.sub_groups.float_mv

    all_ids = data.index.levels[1].unique().tolist()
    all_dates = data.index.levels[0].tolist()
    float_mv = data_source.load_factor('float_mkt_value',ids=all_ids,dates=all_dates)

    common = data.merge(float_mv, left_index=True, right_index=True, how='left')
    group_info_list = []
    for date in all_dates:
        section_factor = common.ix[date]
        sub_group_id = _add_group_id(section_factor,'float_mkt_value',sub_groups)
        for size_id in range(1, sub_groups+1):
            section_section_factor = section_factor[sub_group_id['group_id'] == size_id]
            group_id = _add_group_id(section_section_factor,factor.axe,N,is_ascending)

            idx = pd.MultiIndex.from_product([[date], group_id.index])
            group_id.index = idx
            group_info_list.append(group_id)

    grouping_info = pd.concat(group_info_list).sort_index()
    grouping_info.index.names = ['date', 'IDs']
    factor.grouping_info['float_mv_neutral'] = grouping_info


grouping_funcs_dict = {'typical':typical_grouping,
                       'industry_neutral':industry_neutral,
                       'float_mv_neutral':float_mv_neutral}



