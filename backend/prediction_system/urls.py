#backend/crud_demo/urls.py

from rest_framework.routers import SimpleRouter

from .views import WaterInfoModelViewSet,LtsmModelViewSet

router = SimpleRouter()
# 这里进行注册路径，并把视图关联上，这里的api地址以视图名称为后缀，这样方便记忆api/WaterInfoModelViewSet
router.register("api/WaterInfoModelViewSet", WaterInfoModelViewSet)
router.register("api/LtsmModelViewSet", LtsmModelViewSet)

urlpatterns = [
]
urlpatterns += router.urls