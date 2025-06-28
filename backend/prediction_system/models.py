#文件backend/crud_demo/models.py

from django.db import models

# Create your models here.
from dvadmin.utils.models import CoreModel


class WaterInfoModel(CoreModel):
    '''
    涌水量信息数据模型，用于预测已知地区的涌水量：
    日期
    经度
    纬度
    高程
    日降雨量
    涌水量
    '''
    date = models.DateField(verbose_name="日期")
    longitude = models.DecimalField(max_digits=15, decimal_places=3,verbose_name="经度")
    latitude = models.DecimalField(max_digits=15, decimal_places=3,verbose_name="纬度")
    altitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="高程")
    rainfall = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="日降水量")
    water_quantity = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="涌水量")

    class Meta:
        db_table = "water_info"
        verbose_name = '涌水量信息表'
        verbose_name_plural = verbose_name
        ordering = ('longitude','latitude','altitude','date')

class LstmTrainStatusModel(CoreModel):
    '''
    Lstm训练情况数据模型，用于记录是否已经导入数据，且是否已经训练：
    经度
    纬度
    高程
    是否训练,0表示未训练，1表示已经训练
    '''
    longitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="经度")
    latitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="纬度")
    altitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="高程")
    # 是否训练字段，使用IntegerField并设置choices参数
    IS_TRAIN_CHOICES = (
        (0, '未训练'),
        (1, '已训练'),
    )
    is_train = models.IntegerField(
        choices=IS_TRAIN_CHOICES,
        default=0,
        verbose_name="该点模型是否训练"
    )

    class Meta:
        db_table = "lstm_train_status"
        verbose_name = 'LSTM训练状态表'
        verbose_name_plural = verbose_name
        ordering = ('longitude', 'latitude', 'altitude')

class WaterLevelModel(CoreModel):
    '''
    水位信息数据模型，用于记录指定位置的水位数据：
    日期
    经度
    纬度
    高程
    水位
    '''
    date = models.DateField(verbose_name="日期")
    longitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="经度")
    latitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="纬度")
    altitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="高程")
    water_level = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="水位")

    class Meta:
        db_table = "water_level"
        verbose_name = '水位信息表'
        verbose_name_plural = verbose_name
        ordering = ('longitude', 'latitude', 'altitude', 'date')

class WaterQualityModel(CoreModel):
    '''
    水质信息数据模型，用于管理水质点的相关信息：
    经度
    纬度
    高程
    地层岩性
    硫酸根离子浓度
    碳酸根离子浓度
    溶解性总固体
    pH
    钙镁比值
    8-H
    8-O
    '''
    longitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="经度")
    latitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="纬度")
    altitude = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="高程")
    stratigraphic_lithology = models.CharField(max_length=255, verbose_name="地层岩性")
    sulfate_ion_concentration = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="硫酸根离子浓度")
    carbonate_ion_concentration = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="碳酸根离子浓度")
    total_dissolved_solids = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="溶解性总固体")
    ph = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="pH")
    calcium_magnesium_ratio = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="钙镁比值")
    eight_h = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="8-H")
    eight_o = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="8-O")

    class Meta:
        db_table = "water_quality"
        verbose_name = '水质信息表'
        verbose_name_plural = verbose_name
        ordering = ('longitude', 'latitude', 'altitude')

class BPTrainStatusModel(CoreModel):
    '''
    BP 模型训练情况数据模型，用于记录 BP 模型的训练信息：
    模型名称
    训练时间
    训练状态，0表示训练失败、1表示训练成功
    训练集 RMSE
    测试集 RMSE
    '''
    model_name = models.CharField(max_length=255, verbose_name="模型名称")
    training_time = models.DateTimeField(auto_now_add=True, verbose_name="训练时间")
    # 训练状态字段，使用 IntegerField 并设置 choices 参数
    TRAIN_STATUS_CHOICES = (
        (0, '训练失败'),
        (1, '训练成功'),
    )
    train_status = models.IntegerField(
        choices=TRAIN_STATUS_CHOICES,
        default=0,
        verbose_name="训练状态"
    )
    train_rmse = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="训练集 RMSE")
    test_rmse = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="测试集 RMSE")

    class Meta:
        db_table = "bp_train_status"
        verbose_name = 'BP 模型训练状态表'
        verbose_name_plural = verbose_name
        ordering = ('-training_time',)