import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";

//此处为crudOptions配置
export default function ({ crudExpose}: { crudExpose: CrudExpose}): CreateCrudOptionsRet {
    const pageRequest = async (query: any) => {
        return await api.GetList(query);
    };
    const editRequest = async ({ form, row }: EditReq) => {
        if (row.id) {
            form.id = row.id;
        }
        return await api.UpdateObj(form);
    };
    const delRequest = async ({ row }: DelReq) => {
        return await api.DelObj(row.id);
    };
    const addRequest = async ({ form }: AddReq) => {
        return await api.AddObj(form);
    };

    const exportRequest = async (query: UserPageQuery) => {
        return await api.exportData(query)
    };

    return {
        crudOptions: {
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
            },
            actionbar: {
                buttons: {
                    export:{
                        // 注释编号:django-vue3-admin-crud210716:注意这个auth里面的值，最好是使用index.vue文件里面的name值并加上请求动作的单词
                        show: auth('WaterQualityModelViewSet:Export'),
                        text:"导出",//按钮文字
                        title:"导出",//鼠标停留显示的信息
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('WaterQualityModelViewSet:Create'),
                    },
                    deleteAll: {
                        show: auth('WaterQualityModelViewSet:DeleteAll'), // 假设这里有对应的权限检查
                        text: "一键删除",
                        title: "删除所有涌水量信息数据",
                        click() {
                            return api.deleteAllWaterInfo().then(() => {
                                crudExpose.doRefresh(); // 删除成功后刷新列表
                            });
                        }
                    },
                }
            },
            rowHandle: {
                //固定右侧
                fixed: 'right',
                width: 200,
                buttons: {
                    view: {
                        type: 'text',
                        order: 1,
                        show: auth('WaterQualityModelViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('WaterQualityModelViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('WaterQualityModelViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('WaterQualityModelViewSet:Delete')
                    },
                },
            },
            columns: {
                longitude: {
                    title: '经度',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '经度必填' }],
                        component: {
                            placeholder: '请输入经度',
                            // 控制小数位数为3位
                            step: 0.001,
                        },
                    },
                },

                latitude: {
                    title: '纬度',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '纬度必填' }],
                        component: {
                            placeholder: '请输入纬度',
                            step: 0.001,
                        },
                    },
                },
                altitude: {
                    title: '高程',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '高程必填' }],
                        component: {
                            placeholder: '请输入高程',
                            step: 0.001,
                        },
                    },
                },
                stratigraphic_lithology: {
                    title: '地层岩性',
                    type: 'string',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '地层岩性必填' }],
                        component: {
                            placeholder: '请输入地层岩性',
                        },
                    },
                },
                sulfate_ion_concentration: {
                    title: '硫酸根离子浓度',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '硫酸根离子浓度必填' }],
                        component: {
                            placeholder: '请输入硫酸根离子浓度',
                            step: 0.001,
                        },
                    },
                },
                carbonate_ion_concentration: {
                    title: '碳酸根离子浓度',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '碳酸根离子浓度必填' }],
                        component: {
                            placeholder: '请输入碳酸根离子浓度',
                            step: 0.001,
                        },
                    },
                },
                total_dissolved_solids: {
                    title: '溶解性总固体',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '溶解性总固体必填' }],
                        component: {
                            placeholder: '请输入溶解性总固体',
                            step: 0.001,
                        },
                    },
                },
                ph: {
                    title: 'pH',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: 'pH必填' }],
                        component: {
                            placeholder: '请输入pH',
                            step: 0.01,
                        },
                    },
                },
                calcium_magnesium_ratio: {
                    title: '钙镁比值',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '钙镁比值必填' }],
                        component: {
                            placeholder: '请输入钙镁比值',
                            step: 0.001,
                        },
                    },
                },
                eight_h: {
                    title: '8-H',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '8-H必填' }],
                        component: {
                            placeholder: '请输入H同位素',
                            step: 0.001,
                        },
                    },
                },
                eight_o: {
                    title: '8-O',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '8-O必填' }],
                        component: {
                            placeholder: '请输入氧同位素',
                            step: 0.001,
                        },
                    },
                },
            },
        },
    };
}