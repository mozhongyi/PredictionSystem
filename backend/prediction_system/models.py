#文件backend/crud_demo/models.py

from django.db import models

# Create your models here.
from dvadmin.utils.models import CoreModel


class WaterInfoModel(CoreModel):
    '''
    涌水量信息数据模型，用于预测已知地区的涌水量：
    日期
    横坐标
    纵坐标
    高程
    日降雨量
    涌水量
    '''
    date = models.DateField(verbose_name="日期")
    longitude = models.DecimalField(max_digits=30, decimal_places=20,verbose_name="经度")
    latitude = models.DecimalField(max_digits=30, decimal_places=20,verbose_name="纬度")
    altitude = models.DecimalField(max_digits=30, decimal_places=20, verbose_name="高程")
    rainfall = models.DecimalField(max_digits=30, decimal_places=20, verbose_name="日降水量")
    water_quantity = models.DecimalField(max_digits=30, decimal_places=20, verbose_name="涌水量")

    class Meta:
        db_table = "water_info"
        verbose_name = '涌水量信息表'
        verbose_name_plural = verbose_name
        ordering = ('longitude','latitude','altitude','date')