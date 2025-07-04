from datetime import timedelta

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import math, time
from sklearn.metrics import mean_squared_error
import plotly.express as px
import plotly.graph_objects as go
import chardet
import time
import joblib
import os
import logging

import matplotlib
# 设置为 Agg 后端（非交互后端，适合后台绘图，不会弹出窗口）
matplotlib.use('Agg')

import matplotlib.pyplot as plt


# 将数据数据分割集进行滑动窗口
# target:要输入的数据,DataFrame类型     lookback:滑动窗口长度
# test_ratio:测试集默认占比0.1     val_ratio:验证集默认占比0.1
def split_data(target, lookback, test_ratio=0.1, val_ratio=0.1):
    data_raw = target.to_numpy()
    data = []
    x_latest = []

    # 构建序列数据
    for index in range(len(data_raw) - lookback + 1):
        data.append(data_raw[index: index + lookback])

    data = np.array(data)

    # 计算数据集大小
    total_size = data.shape[0]
    test_set_size = int(total_size * test_ratio)
    # 剩余数据集大小
    total_size = total_size - test_set_size
    # 从剩余数据集中拿0.1来当验证集
    val_set_size = int(total_size * val_ratio)
    # 剩下全部当训练集
    train_set_size = total_size - val_set_size

    # 分割数据集
    # 注意:不可以写为y_train = data[:train_set_size, -1, 1:],这样写维度会报错
    x_train = data[:train_set_size, :-1, :]
    y_train = data[:train_set_size, -1, 1:]

    x_val = data[train_set_size:train_set_size + val_set_size, :-1, :]
    y_val = data[train_set_size:train_set_size + val_set_size, -1, 1:]

    x_test = data[train_set_size + val_set_size:, :-1, :]
    y_test = data[train_set_size + val_set_size:, -1, 1:]

    x_latest.append(data_raw[(len(data_raw) - lookback + 1):])
    x_latest = np.array(x_latest);

    return [x_train, y_train, x_val, y_val, x_test, y_test, x_latest]

# LSTM模型
class LSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super(LSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))
        out = self.fc(out[:, -1, :])
        return out

# 简单的日志记录器，支持日志恢复功能
class Logger:
    def __init__(self, log_file_path):
        self.log_file = log_file_path

        # 创建日志目录（如果不存在）
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # 清空日志文件内容或创建新文件
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(f"训练开始: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            print(f"日志写入失败: {e}")

    def log(self, message):
        """记录日志到文件并打印到控制台"""
        print(message)  # 保持原有打印

        # 写入主日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")


# LSTM模型训练单个点的模型
# Data:还未划分的单个点的数据集
# lookback:滑动窗口长度
# hidden_dim:隐藏层的维度或神经元个数
# num_layers:LSTM层数
# output_dim:模型输出的维度
# num_epochs:训练轮数
def LstmModelTrainSingle(Data, lookback = 30, input_dim = 2,hidden_dim = 60,num_layers = 3,output_dim = 1,num_epochs = 1000):
    # 创建日志目录
    os.makedirs('lstm_logs', exist_ok=True)
    # 该目录用于保存最优模型参数
    os.makedirs('lstm_model', exist_ok=True)
    # 该目录用于保存最优模型训练数据标准化格式
    os.makedirs('lstm_scaler', exist_ok=True)
    # 创建可视化图片存储目录
    os.makedirs('lstm_images', exist_ok=True)
    # 提取第一行(index=0)的坐标
    row = Data.iloc[0]
    name = f"({row['longitude']:.3f},{row['latitude']:.3f},{row['altitude']:.3f})"
    try:
        # 创建唯一的日志文件名
        log_file = f"lstm_logs/{name}training.log"
        logger = Logger(log_file)

        logger.log(f"Group: {name}")
        # 提取标签
        target = Data[['rainfall', 'water_quantity']].copy()

        # 获取最新的一天
        latest_date = Data['date'].iloc[-1]  # 读取最后一行的日期
        # 计算后一天
        next_day = latest_date + timedelta(days=1)

        # 归一化
        scaler = MinMaxScaler(feature_range=(-1, 1))
        target['rainfall'] = scaler.fit_transform(target['rainfall'].values.reshape(-1, 1))
        target['water_quantity'] = scaler.fit_transform(target['water_quantity'].values.reshape(-1, 1))

        best_scaler_path = 'lstm_scaler/' + f'{name}' + 'best_scaler.pkl'
        logger.log('模型标准化格式保存路径：' + best_scaler_path)

        # 保存标准化参数
        joblib.dump(scaler, best_scaler_path)

        x_train, y_train, x_val, y_val, x_test, y_test, x_latest = split_data(target, lookback)
        print('x_train.shape = ', x_train.shape)
        print('y_train.shape = ', y_train.shape)
        print('x_val.shape = ', x_val.shape)
        print('y_val.shape = ', y_val.shape)
        print('x_test.shape = ', x_test.shape)
        print('y_test.shape = ', y_test.shape)
        print('x_latest.shape = ', x_latest.shape)

        # 转换成张量,神经网络模型的数据要求为张量类型
        x_train = torch.from_numpy(x_train).type(torch.Tensor)
        x_test = torch.from_numpy(x_test).type(torch.Tensor)
        x_val = torch.from_numpy(x_val).type(torch.Tensor)
        y_train_lstm = torch.from_numpy(y_train).type(torch.Tensor)
        y_val_lstm = torch.from_numpy(y_val).type(torch.Tensor)
        y_test_lstm = torch.from_numpy(y_test).type(torch.Tensor)
        x_latest_tensor = torch.from_numpy(x_latest).type(torch.Tensor)

        # 模型实例化准备开始训练
        model = LSTM(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim, num_layers=num_layers)
        criterion = torch.nn.MSELoss()
        optimiser = torch.optim.Adam(model.parameters(), lr=0.01)

        hist = np.zeros(num_epochs)
        start_time = time.time()
        best_val_loss = float('inf')  # 用于保存验证集上的最佳损失
        best_model_path = 'lstm_model/' + f'{name}' + 'best_model.pth'  # 最佳模型保存路径
        val_hist = np.zeros(num_epochs)  # 记录验证损失
        logger.log('最优模型参数保存路径：' + best_model_path)

        for t in range(num_epochs):
            # 训练模式
            model.train()

            y_train_pred = model(x_train)

            loss = criterion(y_train_pred, y_train_lstm)
            logger.log("Epoch " + str(t) + " MSE: " + str(loss.item()))
            hist[t] = loss.item()

            optimiser.zero_grad()
            loss.backward()
            optimiser.step()

            # 验证模式
            model.eval()
            with torch.no_grad():  # 禁用梯度计算
                y_val_pred = model(x_val)
                # 反归一化
                y_val_pred_1 = scaler.inverse_transform(y_val_pred.detach().numpy())
                y_val_1 = scaler.inverse_transform(y_val_lstm.detach().numpy())
                val_loss = math.sqrt(mean_squared_error(y_val_1[:, 0], y_val_pred_1[:, 0]))
                # print("Epoch ", t, "val RMSE: ", val_loss)
                logger.log("Epoch " + str(t) + " val RMSE: " + str(val_loss))
                val_hist[t] = val_loss

                # 如果验证损失更好，则保存模型
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    torch.save(model.state_dict(), best_model_path)
                    # print(f"Best model saved at epoch {t} with Test RMSE: {best_val_loss}")
                    logger.log(f"Best model saved at epoch {t} with Test RMSE: {best_val_loss}")

        training_time = time.time() - start_time
        # print("Training time: {}".format(training_time))
        logger.log("Training time: {}".format(training_time))
        logger.log(f"{name} 训练完成\n")

        # 模型结果可视化
        predict = pd.DataFrame(scaler.inverse_transform(y_train_pred.detach().numpy()))
        original = pd.DataFrame(scaler.inverse_transform(y_train_lstm.detach().numpy()))
        sns.set_style("darkgrid")
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.2, wspace=0.2)
        plt.subplot(1, 2, 1)
        ax = sns.lineplot(x=original.index, y=original[0], label="origin", color='royalblue')
        ax = sns.lineplot(x=predict.index, y=predict[0], label="predict", color='tomato')
        ax.set_title(f'{name}训练集LSTM预测结果对比', size=14, fontweight='bold', fontfamily=["SimHei"])
        ax.set_xlabel("Time", size=14)
        ax.set_ylabel("Data", size=14)
        ax.set_xticklabels('', size=10)

        plt.subplot(1, 2, 2)
        ax = sns.lineplot(data=hist, color='royalblue')
        ax.set_xlabel("Epoch", size=14)
        ax.set_ylabel("Loss", size=14)
        ax.set_title(f'{name} Trainset Loss', size=14, fontweight='bold')
        fig.set_figheight(6)
        fig.set_figwidth(16)
        # 保存训练集可视化结果到指定目录
        image_path = f'./lstm_images/{name}LSTM训练集可视化结果.png'
        plt.savefig(image_path, dpi=300, bbox_inches="tight")
        logger.log(f'./lstm_images/{name}LSTM训练集可视化结果.png保存成功')
        # plt.show()

        # 加载最优模型参数
        model.load_state_dict(torch.load(best_model_path, weights_only=True))
        model.eval()  # 将模型设置为评估模式

        # 加载归一化格式
        scaler = joblib.load(best_scaler_path)

        # 在测试集上验证
        with torch.no_grad():  # 禁用梯度计算
            y_test_pred = model(x_test)
            y_train_pred = model(x_train)
            y_val_pred = model(x_val)
            y_latest_pred = model(x_latest_tensor)

        # 归一化数据回到原来状态
        y_train_pred = scaler.inverse_transform(y_train_pred.detach().numpy())
        y_train = scaler.inverse_transform(y_train_lstm.detach().numpy())
        y_val_pred = scaler.inverse_transform(y_val_pred.detach().numpy())
        y_val = scaler.inverse_transform(y_val_lstm.detach().numpy())
        y_test_pred = scaler.inverse_transform(y_test_pred.detach().numpy())
        y_test = scaler.inverse_transform(y_test_lstm.detach().numpy())
        y_latest_pred = scaler.inverse_transform(y_latest_pred.detach().numpy())

        # 计算训练集、验证集和测试集的均方误差
        trainScore = math.sqrt(mean_squared_error(y_train[:, 0], y_train_pred[:, 0]))
        logger.log('Train Score: %.2f RMSE' % (trainScore))
        valScore = math.sqrt(mean_squared_error(y_val[:, 0], y_val_pred[:, 0]))
        logger.log('Train Score: %.2f RMSE' % (valScore))
        testScore = math.sqrt(mean_squared_error(y_test[:, 0], y_test_pred[:, 0]))
        logger.log('Test Score: %.2f RMSE' % (testScore))

        # 制作可视化数据集
        new_target = target[['water_quantity']]

        # 转换数据
        trainPredictPlot = np.empty((len(new_target) + 1, new_target.shape[1]))
        trainPredictPlot[:] = np.nan  # 初始化为NaN
        trainPredictPlot[lookback - 1:len(y_train_pred) + lookback - 1, :] = y_train_pred

        valPredictPlot = np.empty((len(new_target) + 1, new_target.shape[1]))
        valPredictPlot[:] = np.nan  # 初始化为NaN
        valPredictPlot[len(y_train_pred) + lookback - 1:len(y_train_pred) + lookback - 1 + len(y_val_pred),
        :] = y_val_pred

        testPredictPlot = np.empty((len(new_target) + 1, new_target.shape[1]))
        testPredictPlot[:] = np.nan  # 初始化为NaN
        testPredictPlot[len(y_train_pred) + lookback - 1 + len(y_val_pred):-1, :] = y_test_pred

        original = scaler.inverse_transform(target['water_quantity'].values.reshape(-1, 1))
        originPlot = np.empty((len(new_target) + 1, new_target.shape[1]))
        originPlot[:] = np.nan  # 初始化为NaN
        originPlot[0:original.shape[0], :] = original

        latestPredictPlot = np.empty((len(new_target) + 1, new_target.shape[1]))
        latestPredictPlot[:] = np.nan  # 初始化为NaN
        latestPredictPlot[-1:, :] = y_latest_pred

        predictions = np.append(trainPredictPlot, valPredictPlot, axis=1)
        predictions = np.append(predictions, testPredictPlot, axis=1)
        predictions = np.append(predictions, originPlot, axis=1)
        predictions = np.append(predictions, latestPredictPlot, axis=1)
        result = pd.DataFrame(predictions)

        # 将集合好的result画图可视化
        fig = go.Figure()
        fig.add_trace(go.Scatter(go.Scatter(x=result.index, y=result[0],
                                            mode='lines',
                                            name='Train prediction')))
        fig.add_trace(go.Scatter(x=result.index, y=result[1],
                                 mode='lines',
                                 name='Val prediction'))
        fig.add_trace(go.Scatter(go.Scatter(x=result.index, y=result[2],
                                            mode='lines',
                                            name='Test prediction')))
        fig.add_trace(go.Scatter(go.Scatter(x=result.index, y=result[3],
                                            mode='lines',
                                            name='Actual Value')))
        # 新增预测最新值的散点图（明显标注的点+数值标签）
        fig.add_trace(go.Scatter(
            x=result.index,
            y=result[4],  # 第5列：预测最新值
            mode='markers+text',  # 同时显示标记点和文本
            name=f'{next_day} Predict Latest Value',
            marker=dict(
                size=12,  # 点的大小
                color='red',  # 点的颜色
                symbol='circle',  # 点的形状
                line=dict(  # 点的边框
                    width=2,
                    color='white'
                ),
                opacity=0.8  # 点的透明度
            ),
            text=[f"{y:.2f}" for y in result[4]],  # 标签文本（保留两位小数）
            textposition='top center',  # 文本位置（点的上方居中）
            textfont=dict(
                family="Rockwell",
                size=14,
                color="white"
            )
        ))
        fig.update_layout(
            title={
                'text': f'{name}真实值vs预测值',  # 替换为您的标题文本
                'x': 0.5,  # 标题水平居中
                'xanchor': 'center',
                'y': 0.9,  # 标题在图表的顶部
                'yanchor': 'top',
                'font': {
                    'family': "Rockwell",
                    'size': 20,
                    'color': 'white'
                }
            },
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=False,
                linecolor='white',
                linewidth=2
            ),
            yaxis=dict(
                title_text="Value",
                title_font=dict(
                    family='Rockwell',
                    size=12,
                    color='white',
                ),
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor='white',
                linewidth=2,
                ticks='outside',
                tickfont=dict(
                    family='Rockwell',
                    size=12,
                    color='white',
                ),
            ),
            showlegend=True,
            template='plotly_dark'

        )

        annotations = []
        annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                                xanchor='left', yanchor='bottom',
                                text='Results (LSTM)',
                                font=dict(family='Rockwell',
                                          size=26,
                                          color='white'),
                                showarrow=False))
        fig.update_layout(annotations=annotations)
        # 保存可视化结果
        image_path = f'./lstm_images/{name}真实值vs预测值.png'
        fig.write_image(image_path, width=1200, height=600, scale=2,engine='orca')
        logger.log(f'./lstm_images/{name}真实值vs预测值.png保存成功')
        # fig.show()
    except Exception as e:
        logger.log(f"{name}训练过程中发生错误: {str(e)}")
        return f'{name}训练失败:{str(e)}'
    return 'success'
