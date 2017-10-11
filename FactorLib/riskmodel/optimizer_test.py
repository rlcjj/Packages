# coding: utf-8

"""
优化器测试文件
使用兴业风格VG因子作为选股信号
"""
from datetime import datetime
from FactorLib.riskmodel.optimizer import Optimizer
from FactorLib.data_source.base_data_source_h5 import data_source, tc
import pandas as pd

optimal_assets = []
for date in tc.get_trade_days('20140901', '20170831', freq='1m', retstr=None):
    # date = datetime(2017, 2, 24)
    secID = '000905'
    signal_name = 'StyleFactor_VG'
    stockIDs = data_source.sector.get_index_members(ids=secID, dates=[date])
    # stockIDs = stockIDs[stockIDs.iloc[:, 0] == 1.0]
    # stockIDs = drop_suspendtrading(stockIDs)    # 剔除停牌股票
    stockIDs = stockIDs[stockIDs.iloc[:, 0] == 1.0].index.get_level_values(1).tolist()
    signal = data_source.load_factor(signal_name, '/XYData/StyleFactor/',
                                     dates=[date])[signal_name].reset_index(level=0, drop=True)

    opt = Optimizer(signal, stockIDs, date, ds_name='uqer', benchmark=secID)
    opt.add_constraint('StockLimit', default_max=0.08)
    opt.add_constraint('Style', {'MOMENTUM': 0.0, 'RESVOL': 0.0})
    # opt.add_constraint('TrackingError', 0.0025)
    opt.add_constraint('Indu')
    opt.solve()

    if opt.optimal:
        print("%s 权重优化成功" % date.strftime("%Y%m%d"))
        optimal_assets.append(opt.asset)
        style_expo, indu_expo, terr = opt.check_ktt()
optimal_assets = pd.concat(optimal_assets)
optimal_assets.to_csv(r"D:\spyder\stocklist_indnur_mom_vol.csv")
