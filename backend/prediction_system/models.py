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