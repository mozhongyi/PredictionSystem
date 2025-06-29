import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";
import {getLog,get_bp_image} from "/@/views/prediction_system/BPTrainStatusModelViewSet/api";

// 定义表单数据类型
interface FormDataType {
    model_name: string;
}

// 定义预测表单数据类型
interface PredictionFormData {
    longitude: number;
    latitude: number;
    altitude: number;
    model_name: string;
    prediction: string; // 添加预测结果属性
}

//此处为crudOptions配置
export default function ({ crudExpose}: { crudExpose: CrudExpose}): CreateCrudOptionsRet {
    const pageRequest = async (query: any) => {
        return await api.GetList(query);
    };
    // 定义预测请求函数
    const predictRequest = async (formData: PredictionFormData) => {
        try {
            const response = await request({
                url: api.apiPrefix + 'predict-water-quality/',
                method: 'post',
                data: formData
            });
            return response;
        } catch (error) {
            console.error('预测失败:', error);
            return null;
        }
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
        const { model_name } = form;

        let pollInterval: any = null; // 轮询定时器
        let logTextarea: HTMLTextAreaElement | null = null; // 日志文本框引用
        let closeButton: HTMLButtonElement | null = null; // 关闭按钮引用
        let isTrainingCompleted = false; // 训练是否完成标志
        try {
            // 1. 训练开始即创建日志显示框
            logTextarea = document.createElement('textarea');
            logTextarea.value = '训练开始';
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
                        console.log('model_name:',model_name);
                        const logResponse = await getLog(model_name);
                        console.log('logResponse : ', logResponse);
                        if (logResponse.status === '200') {
                            logTextarea.value = logResponse.data;
                            // 滚动到日志底部
                            logTextarea.scrollTop = logTextarea.scrollHeight;
                        }
                    } catch (error) {
                        logTextarea.value += `\n获取日志失败: ${error.message}`;
                    }
                }, 400); // 1秒轮询一次
            }

            startPolling()

        } catch (error) {
            // 刷新列表
            crudExpose.doRefresh();
            // 处理训练失败的情况
            console.error('训练失败:', error);
        } finally {
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
            }, 25000);

            crudExpose.doRefresh();
        }

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
                        show: auth('BPTrainStatusModelViewSet:Export'),
                        text:"导出",//按钮文字
                        title:"导出",//鼠标停留显示的信息
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('BPTrainStatusModelViewSet:Create'),
                        text: '添加模型'
                    },
                    deleteAll: {
                        show: auth('BPTrainStatusModelViewSet:DeleteAll'), // 假设这里有对应的权限检查
                        text: "一键删除",
                        title: "删除所有BP模型信息数据",
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
                width: 250,
                buttons: {
                    view: {
                        type: 'text',
                        order: 1,
                        show: auth('BPTrainStatusModelViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('BPTrainStatusModelViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('BPTrainStatusModelViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('BPTrainStatusModelViewSet:Delete')
                    },
                    trainLog:{
                        type: 'text',
                        order: 5,
                        show: auth('BPTrainStatusModelViewSet:GetLog'),
                        text: '训练日志',
                        click: async ({ row }) =>{
                            try{
                                const { model_name } = row;
                                const response = await getLog( model_name );
                                console.log('response 对象:',response)
                                console.log('response.status = ',response.status)
                                if (response.status === '200')
                                {
                                    const logContent = response.data;
                                    // 创建一个文本框元素
                                    const textarea = document.createElement('textarea');
                                    textarea.value = logContent;
                                    textarea.style.width = '60%';
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
                        show: auth('BPTrainStatusModelViewSet:GetLstmVisualization'),
                        text: '可视化',
                        click: async ({ row }) =>{
                            try{
                                const modelName = row;
                                const response = await get_bp_image(modelName);
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
                    },

                    // 添加“预测”按钮
                    predict: {
                        type: 'text',
                        order: 8,
                        show: auth('BPTrainStatusModelViewSet:Predict'),
                        text: '预测',
                        click: async ({ row }) => {
                            const { model_name } = row;
                            const formData: PredictionFormData = {
                                longitude: 0,
                                latitude: 0,
                                altitude: 0,
                                model_name,
                                prediction: '0'
                            };

                            // 创建表单元素
                            const form = document.createElement('form');
                            form.style.width = '500px';
                            form.style.height = '300px';
                            form.style.padding = '50px';
                            form.style.border = '4px solid #ccc';
                            form.style.borderRadius = '5px';
                            form.style.position = 'fixed';
                            form.style.top = '50%';
                            form.style.left = '50%';
                            form.style.transform = 'translate(-50%, -50%)';
                            form.style.zIndex = '9999';
                            form.style.backgroundColor = 'white';

                            // 创建经度输入框
                            const longitudeInput = document.createElement('input');
                            longitudeInput.type = 'number';
                            longitudeInput.placeholder = '请输入经度';
                            longitudeInput.style.width = '100%';
                            longitudeInput.step = '0.001'; // 限制精度为3位小数
                            longitudeInput.style.marginBottom = '30px';
                            form.appendChild(longitudeInput);

                            // 创建纬度输入框
                            const latitudeInput = document.createElement('input');
                            latitudeInput.type = 'number';
                            latitudeInput.placeholder = '请输入纬度';
                            latitudeInput.style.width = '100%';
                            latitudeInput.step = '0.001'; // 限制精度为3位小数
                            latitudeInput.style.marginBottom = '30px';
                            form.appendChild(latitudeInput);

                            // 创建高程输入框
                            const altitudeInput = document.createElement('input');
                            altitudeInput.type = 'number';
                            altitudeInput.placeholder = '请输入高程';
                            altitudeInput.style.width = '100%';
                            altitudeInput.step = '0.001'; // 限制精度为3位小数
                            altitudeInput.style.marginBottom = '50px';
                            form.appendChild(altitudeInput);

                            // 创建提交按钮
                            const submitButton = document.createElement('button');
                            submitButton.type = 'submit';
                            submitButton.textContent = '提交';
                            submitButton.style.width = '100%';
                            submitButton.style.padding = '10px';
                            submitButton.style.backgroundColor = '#007bff';
                            submitButton.style.color = 'white';
                            submitButton.style.border = 'none';
                            submitButton.style.borderRadius = '5px';
                            form.appendChild(submitButton);

                            // 创建结果显示区域
                            const resultDiv = document.createElement('div');
                            resultDiv.style.marginTop = '10px';
                            resultDiv.style.padding = '10px';
                            resultDiv.style.borderRadius = '5px';
                            form.appendChild(resultDiv);

                            // 创建关闭按钮
                            const closeButton = document.createElement('button');
                            closeButton.textContent = '关闭';
                            closeButton.style.position = 'absolute';
                            closeButton.style.top = '10px';
                            closeButton.style.right = '10px';
                            closeButton.style.backgroundColor = 'red';
                            closeButton.style.color = 'white';
                            closeButton.style.border = 'none';
                            closeButton.style.borderRadius = '5px';
                            closeButton.addEventListener('click', () => {
                                document.body.removeChild(form);
                            });
                            form.appendChild(closeButton);

                            // 将表单添加到页面中
                            document.body.appendChild(form);

                            // 处理表单提交事件
                            form.addEventListener('submit', async (event) => {
                                event.preventDefault();

                                // 简单验证输入
                                if (!longitudeInput.value || !latitudeInput.value || !altitudeInput.value) {
                                    resultDiv.textContent = '请填写所有字段';
                                    resultDiv.style.backgroundColor = '#ffebee'; // 浅红色背景
                                    return;
                                }

                                // 重置结果区域样式
                                resultDiv.textContent = '正在请求...';
                                resultDiv.style.backgroundColor = '#e8f5e9'; // 浅绿色背景

                                formData.longitude = parseFloat(longitudeInput.value);
                                formData.latitude = parseFloat(latitudeInput.value);
                                formData.altitude = parseFloat(altitudeInput.value);

                                try {
                                    const response = await predictRequest(formData);
                                    console.log('完整响应对象:', response); // 检查完整响应结构

                                    // 动态查找 prediction 字段（兼容多种可能的结构）
                                    let predictionValue;

                                    // 情况1：接口返回 { data: { prediction: ... } }
                                    if (response && response.data && typeof response.data.prediction === 'number') {
                                        predictionValue = response.data.prediction.toFixed(3);
                                    }
                                    // 情况2：接口返回 { prediction: ... }（扁平化结构）
                                    else if (response && typeof response.prediction === 'number') {
                                        predictionValue = response.prediction.toFixed(3);
                                    }
                                    // 情况3：其他嵌套结构（如 { result: { prediction: ... } }）
                                    else if (response && response.result && typeof response.result.prediction === 'number') {
                                        predictionValue = response.result.prediction.toFixed(3);
                                    }
                                    else {
                                        throw new Error('未找到有效的预测结果字段');
                                    }

                                    // 更新表单数据并显示结果
                                    formData.prediction = predictionValue;
                                    resultDiv.textContent = `预测结果: ${predictionValue}`;
                                    resultDiv.style.backgroundColor = '#e8f5e9';
                                } catch (error) {
                                    console.error('预测流程异常:', error);
                                    resultDiv.textContent = `请求出错：${error.message}`;
                                    resultDiv.style.backgroundColor = '#ffebee';
                                }
                            });
                        }
                    }
                },
            },
            columns: {
                model_name: {
                    title: '模型名称',
                    type: 'string',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '模型名称必填' }],
                        component: {
                            placeholder: '请输入模型名称',
                        },
                    },
                },
                training_time: {
                    title: '训练时间',
                    type: 'datetime',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },
                train_status: {
                    title: '训练状态',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                        formatter: (row: any) => {
                            return row.train_status === 0 ? '训练失败' : '训练成功';
                        }
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },
                train_rmse: {
                    title: '训练集 RMSE',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },
                test_rmse: {
                    title: '测试集 RMSE',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },

            },
        },
    };
}

