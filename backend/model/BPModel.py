import pprint

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
# 设置为 Agg 后端（非交互后端，适合后台绘图，不会弹出窗口）
matplotlib.use('Agg')
import os
import time,math
import joblib
from datetime import datetime

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

# 计算三维空间中两点的欧氏距离
def calculate_3d_distance(lon1, lat1, elev1, lon2, lat2, elev2):
    dx = (lon2 - lon1)
    dy = (lat2 - lat1)
    dz = elev2 - elev1  # 高程差
    return np.sqrt(dx**2 + dy**2 + dz**2)

# 混合填充时间序列缺失值：
#   - 若连续缺失天数 > threshold_days，用列均值填充
#   - 若连续缺失天数 <= threshold_days，用线性插值填充
#   - 确保时间索引连续并按天重采样
def hybrid_fill(df, threshold_days=3):
    # 确保时间索引连续并按天重采样
    df = df.resample('D').asfreq()

    for col in df.columns:
        ser = df[col].copy()
        mask = ser.isna()
        missing_count = df[col].isna().sum()
        if missing_count == 0:
            continue

        # 标记连续缺失段
        shift_mask = mask.ne(mask.shift())
        groups = shift_mask.cumsum()
        # 仅关注缺失段（mask=True）
        missing_blocks = groups[mask].reset_index()

        # 按段分组处理
        for _, block in missing_blocks.groupby(col):  # 根据每一列进行分组
            # 获取缺失段起止日期
            start = block['date'].min()
            end = block['date'].max()
            days_missing = (end - start).days + 1
            print(f"处理缺失段: {start} 到 {end}, 缺失天数: {days_missing}")

            if days_missing > threshold_days:
                # 长缺失段：列均值填充
                ser.loc[start:end] = ser.mean()
                print(f"长缺失段填充均值: {ser.mean()}")
            else:
                # 短缺失段：尝试线性插值
                prev_idx = ser.loc[:start - pd.Timedelta(days=1)].last_valid_index()
                next_idx = ser.loc[end + pd.Timedelta(days=1):].first_valid_index()

                if prev_idx is not None and next_idx is not None:
                    prev_val = ser.loc[prev_idx]
                    next_val = ser.loc[next_idx]

                    # 计算插值序列
                    num_missing = days_missing
                    interp_values = np.linspace(prev_val, next_val, num=num_missing + 2)[1:-1]
                    ser.loc[start:end] = interp_values
                else:
                    # 边界缺失：退化为均值填充
                    ser.loc[start:end] = ser.mean()

        # 更新列数据
        df[col] = ser
        #print(f"填充后的列数据:")
        #print(ser)

    return df

# waterInfo:涌水量的DataFrame
# waterLevel:水位的DateFrame
# 该函数将涌水量与水位的数据进行合并
def process_1(waterInfo,waterLevel):
    waterLevel['date'] = pd.to_datetime(waterLevel['date'])
    waterInfo['date'] = pd.to_datetime(waterInfo['date'])
    waterLevel = waterLevel.drop(['id','description','modifier','dept_belong_id','update_datetime','create_datetime','creator_id'], axis=1)
    waterInfo = waterInfo.drop(['id', 'description', 'modifier', 'dept_belong_id', 'update_datetime', 'create_datetime', 'creator_id'], axis=1)
    pprint.pprint(waterInfo)
    pprint.pp(waterLevel)

    # 复制涌水量DataFrame作为结果基础
    result_df = waterInfo.copy()

    # 对水位数据按经纬度高程分组
    level_groups = waterLevel.groupby(['longitude', 'latitude', 'altitude'])
    # 遍历每个水位分组
    for group_idx, (wl_lon, wl_lat, wl_elev) in enumerate(level_groups.groups.keys(), 1):
        # 提取当前分组数据
        group_data = level_groups.get_group((wl_lon, wl_lat, wl_elev))

        # 添加水位组的经纬度高程信息(分开为独立列)
        result_df[f'水位组_{group_idx}_经度'] = wl_lon
        result_df[f'水位组_{group_idx}_纬度'] = wl_lat
        result_df[f'水位组_{group_idx}_高程'] = wl_elev

        # 计算三维距离（向量化操作）
        result_df[f'水位组_{group_idx}_距离'] = result_df.apply(
            lambda row: calculate_3d_distance(
                row['longitude'], row['latitude'], row['altitude'],
                wl_lon, wl_lat, wl_elev
            ),
            axis=1
        )

        # 按日期匹配水位值
        matched = pd.merge(
            result_df,
            group_data[['date', 'water_level']],
            on='date',
            how='left'
        )
        # 重命名水位列并保留结果
        matched = matched.rename(columns={'water_level': f'水位组_{group_idx}_水位'})
        result_df = matched[result_df.columns.tolist() + [f'水位组_{group_idx}_水位']]

    return result_df

# 全连接神经网络,需要传入输入数据的纬度
class RegressionModel(nn.Module):
    def __init__(self, input_size):
        super(RegressionModel, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)  # 输入层 -> 隐藏层 1
        self.fc2 = nn.Linear(128, 64)          # 隐藏层 1 -> 隐藏层 2
        self.fc3 = nn.Linear(64, 32)           # 隐藏层 2 -> 输出层
        self.fc4 = nn.Linear(32, 1)
        self.relu = nn.ReLU()                 # 激活函数

    def forward(self, x):
        x = self.relu(self.fc1(x))  # 隐藏层 1
        x = self.relu(self.fc2(x))  # 隐藏层 2
        x = self.relu(self.fc3(x))  # 隐藏层 2
        x = self.fc4(x)             # 输出层
        return x

# modelName:模型名称
# waterInfo:涌水量的DataFrame
# waterLevel:水位的DateFrame
def BPTrain(modelName,waterInfo,waterLevel):
    # 设置支持中文的字体
    plt.rcParams['font.family'] = 'SimHei'  # 可以根据系统情况替换为其他支持中文的字体
    # 解决负号显示问题
    plt.rcParams['axes.unicode_minus'] = False

    # 该目录用于保存最优模型参数
    os.makedirs('bp_models', exist_ok=True)

    # 该目录用于保存最优模型训练数据标准化格式
    os.makedirs('bp_scalers', exist_ok=True)

    # 该目录用于保存可视化图片
    os.makedirs('bp_images', exist_ok=True)

    # 该目录用于保存日志文件
    os.makedirs('bp_logs', exist_ok=True)
    # 创建唯一的日志文件名
    log_file = f"bp_logs/{modelName}training.log"
    logger = Logger(log_file)

    # 记录是否训练成功
    train_status = 0;

    # 将涌水量和水位数据进行合并
    merged_data = process_1(waterInfo,waterLevel)

    # 按'横坐标', '纵坐标', '高程'进行分组
    grouped = merged_data.groupby(['longitude', 'latitude', 'altitude'])
    df_list = []

    # 合并后的数据分组进行填充
    for name, group in grouped:
        print("当前正在处理点：", name)
        # 首先将'日期'列设置为索引
        group.set_index('date', inplace=True)

        df_fill = hybrid_fill(group, 14)

        # 将插值后的数据加入
        df_list.append(df_fill)

    # 使用pd.concat将列表中的所有DataFrame合并成一个单一的DataFrame
    df_fill = pd.concat(df_list, ignore_index=True)
    df_fill = df_fill.round(3)

    # 模型输出实际值
    target = df_fill['water_quantity']
    # 模型输入值
    data = df_fill.drop(['water_quantity'], axis=1)
    pprint.pprint(data)

    X = data.astype(np.float32)  # 特征
    y = target.astype(np.float32).values.reshape(-1, 1)  # 目标值，转换为 NumPy 数组并重塑

    # 第一次划分：分离测试集（10%）
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y,
        test_size=0.1,
        random_state=42
    )

    # 第二次划分：从训练集中分离验证集（10%的剩余数据作为验证集）
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val,
        test_size=0.1,
        random_state=42
    )

    logger.log(f'X_train shape : {X_train.shape}')
    logger.log(f'y_train shape : {y_train.shape}')
    logger.log(f'X_val shape : {X_val.shape}')
    logger.log(f'y_val shape : {y_val.shape}')
    logger.log(f'X_test shape : {X_test.shape}')
    logger.log(f'y_test shape : {y_test.shape}')

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
    X_val_tensor = torch.tensor(X_val_scaled, dtype=torch.float32)
    y_val_tensor = torch.tensor(y_val, dtype=torch.float32)
    X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.float32)

    # 初始化模型
    input_size = X_train.shape[1]
    model = RegressionModel(input_size)
    # 定义损失函数和优化器
    criterion = nn.MSELoss()  # 均方误差损失函数
    optimizer = optim.Adam(model.parameters(), lr=0.001)  # Adam 优化器

    # 训练模型
    num_epochs = 100
    hist = np.zeros(num_epochs)
    best_val_loss = float('inf')  # 用于保存验证集上的最佳损失
    best_train_loss = float('inf')  # 保存训练集上得最佳损失
    val_hist = np.zeros(num_epochs)  # 记录测试损失

    best_model_path = f'bp_models/{modelName}best_model.pth'  # 最佳模型保存路径
    best_scaler_path = f'bp_scalers/{modelName}best_scaler.pkl'  # 模型的scaler保存路径
    logger.log(f'最优模型参数保存路径：{best_model_path}')
    logger.log(f'scaler参数保存路径：{best_model_path}')

    # 保存标准化参数
    joblib.dump(scaler, best_scaler_path)

    start_time = time.time()

    for epoch in range(num_epochs):
        logger.log(f"-------------------第{epoch}次训练----------------------")
        # 训练模式
        model.train()
        # 前向传播
        outputs = model(X_train_tensor)
        loss = criterion(outputs, y_train_tensor)

        y_train_1 = y_train_tensor.detach().numpy()
        y_train_pred = outputs.detach().numpy()

        train_loss = math.sqrt(mean_squared_error(y_train_1[:, 0], y_train_pred[:, 0]))

        logger.log(f"Epoch epoch Train RMSE:{train_loss}")

        # 反向传播和优化
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 记录训练损失
        hist[epoch] = loss.item()

        # 验证模式
        model.eval()
        # 在验证集上评估
        with torch.no_grad():
            y_val_pred = model(X_val_tensor)
            y_val_pred_1 = y_val_pred.detach().numpy()
            y_val_1 = y_val_tensor.detach().numpy()
            val_loss = math.sqrt(mean_squared_error(y_val_1[:, 0], y_val_pred_1[:, 0]))
            logger.log(f"Epoch epoch Val RMSE: {val_loss}")
            val_hist[epoch] = val_loss

            # 如果训练损失和测试损失都更好就修改
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), best_model_path)
                logger.log(f"Best model saved at epoch {epoch} with Val RMSE: {best_val_loss}")

    # 训练成功
    train_status = 1;
    # 获取当前时间并格式化为 "年-月-日_时-分-秒" 格式
    current_time = datetime.now()
    training_time = time.time() - start_time
    logger.log("Training time: {}".format(training_time))

    # 加载最佳模型
    model.load_state_dict(torch.load(best_model_path, weights_only=True))
    model.eval()  # 将模型设置为评估模式
    # 加载标准化格式scaler
    scaler = joblib.load(best_scaler_path)

    with torch.no_grad():
        y_train_pred_tensor = model(X_train_tensor)
        y_test_pred_tensor = model(X_test_tensor)

    y_train_pred = y_train_pred_tensor.numpy()
    y_test_pred = y_test_pred_tensor.numpy()

    # 计算训练集和测试集的均方误差
    trainScore = math.sqrt(mean_squared_error(y_train[:, 0], y_train_pred[:, 0]))
    logger.log('Train Score: %.2f RMSE' % (trainScore))
    testScore = math.sqrt(mean_squared_error(y_test[:, 0], y_test_pred[:, 0]))
    logger.log('Test Score: %.2f RMSE' % (testScore))

    # 制作测试集上的可视化数据集
    testPlot = np.empty_like(y_test)
    testPlot[:, 0] = np.nan
    testPlot[:] = y_test

    testPredictPlot = np.empty_like(y_test_pred)
    testPredictPlot[:, 0] = np.nan
    testPredictPlot[:] = y_test_pred

    print('testPlot shape : ', testPlot.shape)
    print('testPredictPlot shape : ', testPredictPlot.shape)
    predictions = np.append(testPlot, testPredictPlot, axis=1)
    testResult = pd.DataFrame(predictions)
    testResult.columns = ['originData', 'predictData']

    testResult_part = testResult.iloc[0:200]
    # 将集合好的testResult画图可视化
    fig = go.Figure()
    fig.add_trace(go.Scatter(go.Scatter(x=testResult_part.index, y=testResult_part['originData'],
                                        mode='lines',
                                        name='Test Origin')))
    fig.add_trace(go.Scatter(x=testResult_part.index, y=testResult_part['predictData'],
                             mode='lines',
                             name='Test prediction'))
    fig.update_layout(
        title={
            'text': 'Visualization on the Test set',  # 替换为您的标题文本
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
                            text='Results',
                            font=dict(family='Rockwell',
                                      size=26,
                                      color='white'),
                            showarrow=False))
    fig.update_layout(annotations=annotations)

    # 保存可视化结果
    image_path = f'bp_images/{modelName}真实值vs预测值.png'
    fig.write_image(image_path, width=1200, height=600, scale=2, engine='orca')
    logger.log(f'{image_path}保存成功')

    trainScore = round(trainScore,3)
    testScore = round(testScore, 3)

    # 返回训练完毕的时间、训练集RMSE、测试集RMSE、训练完成标志
    return current_time,trainScore,testScore,train_status