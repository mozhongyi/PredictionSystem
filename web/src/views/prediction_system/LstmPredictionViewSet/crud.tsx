import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";

// 导入训练单个点的接口
import { trainSinglePoint,getLog, get_lstm_image } from './api';


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
                        show: auth('LtsmModelViewSet:Export'),
                        text:"导出",//按钮文字
                        title:"导出",//鼠标停留显示的信息
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('LtsmModelViewSet:Create'),
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
                        show: auth('LtsmModelViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('LtsmModelViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('LtsmModelViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('LtsmModelViewSet:Delete')
                    },
                    // 添加“训练”按钮
                    train: {
                        type: 'text',
                        order: 5,
                        show: auth('LtsmModelViewSet:Train'),
                        text: '训练',
                        click: async ({ row }) => {
                            let pollInterval: any = null; // 轮询定时器
                            let logTextarea: HTMLTextAreaElement | null = null; // 日志文本框引用
                            let closeButton: HTMLButtonElement | null = null; // 关闭按钮引用
                            let isTrainingCompleted = false; // 训练是否完成标志
                            try {
                                // 显示加载状态
                                row.loading = true;
                                const { longitude, latitude, altitude } = row;

                                // 1. 训练开始即创建日志显示框
                                logTextarea = document.createElement('textarea');
                                logTextarea.value = '训练开始，正在获取日志...';
                                logTextarea.style.width = '60%';
                                logTextarea.style.height = '600px';
                                logTextarea.style.position = 'fixed';
                                logTextarea.style.top = '50%';
                                logTextarea.style.left = '50%';
                                logTextarea.style.transform = 'translate(-50%, -50%)';
                                logTextarea.style.zIndex = '9999';
                                logTextarea.style.border = '1px solid #ccc';
                                logTextarea.style.padding = '10px';
                                logTextarea.style.backgroundColor = 'white';
                                logTextarea.readOnly = true;

                                closeButton = document.createElement('button');
                                closeButton.textContent = '关闭';
                                closeButton.style.position = 'fixed';
                                closeButton.style.top = 'calc(50% + 300px)';
                                closeButton.style.left = '50%';
                                closeButton.style.transform = 'translateX(-50%)';
                                closeButton.style.zIndex = '10000';
                                closeButton.style.fontSize = '20px';
                                closeButton.style.padding = '10px 20px';
                                closeButton.style.minWidth = '120px';
                                closeButton.style.backgroundColor = 'red';
                                closeButton.style.color = 'white';

                                // 确保清理资源
                                function stopPolling() {
                                    if (pollInterval) {
                                        clearInterval(pollInterval);
                                        pollInterval = null;
                                    }
                                }

                                function removeLogElements() {
                                    if (logTextarea) {
                                        document.body.removeChild(logTextarea);
                                        logTextarea = null;
                                    }
                                    if (closeButton) {
                                        document.body.removeChild(closeButton);
                                        closeButton = null;
                                    }
                                }

                                // 关闭按钮事件：停止轮询并移除元素
                                closeButton.addEventListener('click', () => {
                                    stopPolling();
                                    removeLogElements();
                                });

                                document.body.appendChild(logTextarea);
                                document.body.appendChild(closeButton);

                                // 2. 启动轮询获取日志（每秒一次）
                                function startPolling() {
                                    pollInterval = setInterval(async () => {
                                        if (!logTextarea || isTrainingCompleted) return;
                                        try {
                                            const logResponse = await getLog(longitude, latitude, altitude);
                                            console.log('logResponse : ',logResponse);
                                            if (logResponse.status === '200') {
                                                logTextarea.value = logResponse.data;
                                                // 滚动到日志底部
                                                logTextarea.scrollTop = logTextarea.scrollHeight;
                                            }
                                        } catch (logError) {
                                            logTextarea.value += `\n获取日志失败: ${logError.message}`;
                                        }
                                    }, 1000); // 1秒轮询一次
                                }

                                startPolling(); // 立即开始轮询

                                const response = await trainSinglePoint({ longitude, latitude, altitude });
                                if (response.data.message === '模型训练成功') {
                                    // 更新训练状态为成功
                                    row.trainStatus = "已训练";
                                    // 刷新列表
                                    crudExpose.doRefresh();
                                }
                            } catch (error) {
                                // 刷新列表
                                crudExpose.doRefresh();
                                // 处理训练失败的情况
                                console.error('训练失败:', error);
                            } finally{
                                // 确保清理资源
                                function stopPolling() {
                                    if (pollInterval) {
                                        clearInterval(pollInterval);
                                        pollInterval = null;
                                    }
                                }

                                // 训练结束后等待3秒停止轮询（给日志最后写入时间）
                                setTimeout(() => {
                                    stopPolling();
                                    if (logTextarea) {
                                        logTextarea.value += "\n\n日志获取结束";
                                    }
                                }, 3000);

                                // 训练结束后清理
                                row.loading = false;
                                crudExpose.doRefresh();
                            }

                        }
                    },
                    trainLog:{
                        type: 'text',
                        order: 6,
                        show: auth('LtsmModelViewSet:GetLog'),
                        text: '训练日志',
                        click: async ({ row }) =>{
                            try{
                                const { longitude, latitude, altitude } = row;
                                const response = await getLog( longitude, latitude, altitude );
                                console.log('response 对象:',response)
                                console.log('response.status = ',response.status)
                                if (response.status === '200')
                                {
                                    const logContent = response.data;
                                    // 创建一个文本框元素
                                    const textarea = document.createElement('textarea');
                                    textarea.value = logContent;
                                    textarea.style.width = '80%';
                                    textarea.style.height = '600px';
                                    textarea.style.position = 'fixed';
                                    textarea.style.top = '50%';
                                    textarea.style.left = '50%';
                                    textarea.style.transform = 'translate(-50%, -50%)';
                                    textarea.style.zIndex = '9999';
                                    textarea.style.border = '1px solid #ccc';
                                    textarea.style.padding = '10px';
                                    textarea.style.backgroundColor = 'white';
                                    textarea.readOnly = true;

                                    // 创建一个关闭按钮
                                    const closeButton = document.createElement('button');
                                    closeButton.textContent = '关闭';
                                    closeButton.style.position = 'fixed';
                                    closeButton.style.top = 'calc(50% + 300px)';
                                    closeButton.style.left = '50%';
                                    closeButton.style.transform = 'translateX(-50%)';
                                    closeButton.style.zIndex = '10000';
                                    // 修改按钮样式以增大按钮
                                    closeButton.style.fontSize = '20px'; // 增大字体大小
                                    closeButton.style.padding = '10px 20px'; // 增加内边距
                                    closeButton.style.minWidth = '120px'; // 设置最小宽度
                                    // 设置按钮背景颜色和文字颜色
                                    closeButton.style.backgroundColor = 'red'; // 背景颜色，可根据需要修改
                                    closeButton.style.color = 'white'; // 文字颜色，可根据需要修改
                                    closeButton.addEventListener('click', () => {
                                        document.body.removeChild(textarea);
                                        document.body.removeChild(closeButton);
                                    });

                                    // 将文本框和关闭按钮添加到页面中
                                    document.body.appendChild(textarea);
                                    document.body.appendChild(closeButton);
                                }
                                else
                                {
                                    console.error('获取训练日志失败:', response.data.detail);
                                }


                            } catch (error) {
                                console.error('获取训练日志失败:', error);
                            }
                        }
                    },
                    // 添加“可视化”按钮
                    visualization:{
                        type: 'text',
                        order: 7,
                        show: auth('LtsmModelViewSet:GetLstmVisualization'),
                        text: '可视化',
                        click: async ({ row }) =>{
                            try{
                                const { longitude, latitude, altitude } = row;
                                const response = await get_lstm_image({ longitude, latitude, altitude });
                                if (response.status === 200)
                                {
                                    const imgUrl = URL.createObjectURL(new Blob([response.data], { type: 'image/png' }));
                                    const img = document.createElement('img');
                                    img.src = imgUrl;
                                    img.style.maxWidth = '80%';
                                    img.style.maxHeight = '80%';
                                    img.style.position = 'fixed';
                                    img.style.top = '50%';
                                    img.style.left = '50%';
                                    img.style.transform = 'translate(-50%, -50%)';
                                    img.style.zIndex = '9999';
                                    img.style.border = '1px solid #ccc';
                                    img.style.padding = '10px';
                                    img.style.backgroundColor = 'white';

                                    const closeButton = document.createElement('button');
                                    closeButton.textContent = '关闭';
                                    closeButton.style.position = 'fixed';
                                    closeButton.style.top = 'calc(50% + 40%)';
                                    closeButton.style.left = '50%';
                                    closeButton.style.transform = 'translateX(-50%)';
                                    closeButton.style.zIndex = '10000';

                                    // 修改按钮样式以增大按钮
                                    closeButton.style.fontSize = '20px'; // 增大字体大小
                                    closeButton.style.padding = '10px 20px'; // 增加内边距
                                    closeButton.style.minWidth = '120px'; // 设置最小宽度
                                    // 设置按钮背景颜色和文字颜色
                                    closeButton.style.backgroundColor = 'red'; // 背景颜色，可根据需要修改
                                    closeButton.style.color = 'white'; // 文字颜色，可根据需要修改

                                    closeButton.addEventListener('click', () => {
                                        document.body.removeChild(img);
                                        document.body.removeChild(closeButton);
                                        URL.revokeObjectURL(imgUrl);
                                    });

                                    document.body.appendChild(img);
                                    document.body.appendChild(closeButton);
                                }
                                else
                                {
                                    console.error('获取可视化图片失败:', response.data.detail);
                                }
                            }catch (error) {
                                console.error('获取可视化图片失败:', error);
                            }
                        }
                    }
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
                    search: { show: false },
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
                trainStatus: {
                    title: '训练状态',
                    type: 'text',
                    search: {
                        show: false
                    },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                },
            },
        },
    };
}