# Ar_project
本人参加2020全国大学生物联网设计大赛所做项目负责的软件部分，获得华东赛区特等奖、全国总决赛二等奖。
    该项目包含了导航系统、语音系统、目标检测系统三个部分，涵盖语音唤醒、语音识别、语音合成、语音导航、聊天机器人、目的地搜索、路径规划、车道分割、目标检测(车、车牌、违规车、路标等)、车牌识别等一整套快速解决方案！（附带的两个模型为基于玩具车和模型道路数据集的....）

# 项目技术架构如下图
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/%E6%95%B4%E4%BD%93%E6%A1%86%E6%9E%B61.jpg)

# 目录结构
```c
Project
├─AR_project_PI
│  │  ARPImain.py //树莓派客户端主程序,用于调度树莓派端一切数据传输线程、界面更新、信号处理等，整合树莓派端的语音控制系统、导航系统、数据传输系统
│  │  ARui.py //主界面类，调用webBrowser类实现内嵌浏览器功能，定义所有界面信号的槽函数
│  │  Arrowclass.py //箭头类
│  │  construction.png
│  │  cv2test.py//测试cv2获取摄像头数据最小例子
│  │  foundgreen.mp4//
│  │  foundred.mp4
│  │  get_AndroidGps_server.py //从app获取输入的目的地gps信息
│  │  GPStransformer.py //各种gps坐标转换（没有用到）
│  │  height_limit.png
│  │  MPU6050filter.py
│  │  MPU6065reader.py //陀螺仪传感器数据读取,需要自行测试矫正，安装角度不同初始参数不一样，矫正后可连续使用不漂移
│  │  Navigation_system.py //导航系统类，包含路径规划、目的地搜索、位置更新等
│  │  picameratest.py//使用picameratest测试摄像头最小例子
│  │  pi_clientcv.py //摄像头数据获取与处理、传输类
│  │  resources_rc.py //图标资源
│  │  resources_rc.qrc//资源标注文件，通过pyqrc转换为py文件被调用
│  │  webBrowser.py //基于QWebEngine的内嵌浏览器，可实现大部分浏览器的功能，关键是他可以无头嵌入qt界面中，使用qwebchannel可以调用加载的js函数
│  │  webtest.py //浏览器测试的最小例子
│  │  
│  ├─arrow //箭头图片文件夹
│  │      forward.png//向前箭头
│  │      forward2.png//斜前方箭头
│  │      left.png//向左箭头
│  │      right.png//向右箭头
│  │      
│  ├─Navigationhtml //预设html文件夹
│  │      initpage.html//初始页
│  │      keywordsearch.html//目的地搜索页面
│  │      marker.png
│  │      marker1.png
│  │      navigating.html
│  │      nowpos.html
│  │      pathplan.html
│  │      pathplan00.html
│  │      test.html
│  │      
│  └─voicecontrollermodel //语音系统文件夹
│      │  chatbot.py //聊天机器人类,多轮对话线程
│      │  demo.py//snowboy的测试demo
│      │  lxyysbtest.py//speech_recognition录音最小例子
│      │  Makefile
│      │  snowboy-detect-swig.cc
│      │  snowboy-detect-swig.i
│      │  snowboy-detect-swig.o
│      │  snowboydecoder.py//snowboy依赖文件
│      │  snowboydetect.py//同上
│      │  test.py//语音系统测试例子
│      │  text2voice.py //文字转语音（旧版已遗弃，新的可以看voice_and_text.py文件）
│      │  txpythonsdk.py //腾讯sdk改写的语音合成,需要补充自己的apikey
│      │  voicecontroller.py //语音控制系统基类,汇总了语音唤醒,语音识别,语音合成类等
│      │  voice_and_text.py //文字语音相互转换基类
│      │  _snowboydetect.so
│      │  关闭投影.pmdl//snowboy语音唤醒模型文件
│      │  打开投影.pmdl//snowboy语音唤醒模型文件
│      │  蜂鸟.pmdl //语音唤醒模型文件
│      │  
│      ├─ihere_file //离线的语音应答词
│      │  ...
│      │  ...
│      │      
│      ├─inandoutchating_file //离线的一些语音短语(用于加快响应速度,减少api调用量)
│      │  ...
│      │  ...    
│      │  
│      └─resources //snowboy自带示例
│          │  common.res
│          │  ding.wav
│          │  ding0.wav
│          │  dong.wav
│          │  snowboy.raw
│          │  snowboy.wav
│          │  
│          ├─alexa
│          │  │  alexa_02092017.umdl
│          │  │  SnowboyAlexaDemo.apk
│          │  │  
│          │  └─alexa-avs-sample-app
│          │          alexa.umdl
│          │          avs-kittai.patch
│          │          
│          └─models
│                  computer.umdl
│                  hey_extreme.umdl
│                  jarvis.umdl
│                  neoya.umdl
│                  smart_mirror.umdl
│                  snowboy.umdl
│                  subex.umdl
│                  view_glass.umdl
│                  
├─AR_project_Server //服务端系统
│  │  ali_client.py //向阿里云发送违章数据的客户端线程
│  │  AR_predicter.py //服务端主程序,多进程(没错是多进程)运行,有效提高多核心cpu利用率,主进程专门处理数据传输,另外两个进程分别是图像分割算法和目标检测(包含OCR)
│  │  cv2test.py
│  │  nvideo.mp4 //测试视频
│  │  pi_server.py //与树莓派客户端通信的线程
│  │  websocket.py //与web前端通信的线程
│  │  
│  ├─model //模型文件夹
│  │  ├─DetectionModel //目标检测模型,基于自定义玩具车、玩具红绿灯、玩具路标数据集。。
│  │  │  └─yolov3_mobilenet_v3ndd444blargep
│  │  │          infer_cfg.yml
│  │  │          __model__
│  │  │          __params__
│  │  │          
│  │  └─SegModel //道路分割模型,基于自定义沙盒道路数据集。。
│  │      └─cityscape_fast_scnnnds111
│  │              deploy.yaml
│  │              model
│  │              params
│  │              
│  ├─PaddleDetectiondeploy 
│  │  │  README.md
│  │  │  
│  │  └─python
│  │      │  doinfer.py
│  │      │  infer.py
│  │      │  README.md
│  │      │  visualize.py
│  │      │  
│  │      ├─output
│  │      │      chld0051.jpg
│  │      │      chld0052.jpg
│  │      │      
│  │      └─__pycache__
│  │              doinfer.cpython-37.pyc
│  │              visualize.cpython-37.pyc
│  │              
│  ├─PaddleOCR
│  │  ├─ppocr
│  │  │  ...
│  │  │  ...
│  │  │  
│  │  └─tools
│  │      │  ...
│  │      │  ...
│  │      │  
│  │      ├─eval_utils
│  │      │  ...
│  │      │      
│  │      └─infer
│  │          │  predict_det.py
│  │          │  predict_det000.py
│  │          │  predict_rec.py
│  │          │  predict_rec000.py
│  │          │  predict_system.py
│  │          │  predict_system000.py
│  │          │  utility.py
│  │          │  utility000.py
│  │          │  
│  │           ...      
│  └─PaddleSegdeploy
│      │  README.md
│      │  
│      └─python
│          │  doinfer.py
│          │  infer.py
│          │  README.md
│          │  requirements.txt
│          │  
│          ├─docs
│          │      compile_paddle_with_tensorrt.md
│          │      PaddleSeg_Infer_Benchmark.md
│          │      
│          └─__pycache__
│                  doinfer.cpython-37.pyc
│                  
└─Others //附带的一些脚本
        ali_server.py //阿里云后台后台部署脚本，接收违章数据
        AllPaths.json //写入把违章数据文件名写入json
        仿射变换test.py //仿射变换测试最小示例（已弃用，使用透视变换更好）
        初始化服务端的json路径.py //以下如名
        标注好的图片更改大小.py
        标注好的图片重命名.py
        生成文件名列表.py
        移除不存在文件.py//对标注数据的处理：根据json文件移除图片/根据图片移除json文件
        透视变换test.py//透视变换最小测试示例
        随机分数据集.py//数据分数据集
        随机重命名.py//随机重命名图片用于打乱图片顺序
```
所有关键类的注释都已经打上了，自己慢慢看...各个模块可以单独运行测试
# 实际画面

## 关于投影画面
投影我们采用的是dlp2000充当树莓派的屏幕直接显示，然后在树莓派上运行窗口程序即产生投影Ar效果。有关，dlp模块与树莓派连接可以看[这个](https://blog.csdn.net/qq_25160559/article/details/106062176)
使用树莓派4B需要改一下分辨率，不然会有画面倾斜等，[参考这个](https://e2e.ti.com/support/dlp/f/94/t/850392?DLPDLCR2000EVM-Resolution-problem-settings-with-i2c-and-raspberry-pi)
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200826_200301.jpg)
## 投影效果
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200823_205618.jpg)
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200827_180415.jpg)
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200831_162918.jpg)

# 依赖
paddlepaddle环境，有显卡的安装gpu版本比较好
```
opencv
numpy
pillow
pyqt5
PyQtWebEngine
requests
multiprocess
tencentcloud-sdk-python
```
## 各种api
腾讯api：[参考](https://github.com/tencentyun/qcloud-documents/blob/master/%E5%BC%80%E5%8F%91%E8%80%85%E8%B5%84%E6%BA%90/%E4%BA%91API%20SDK/%E9%80%9A%E7%94%A8%E8%AF%AD%E8%A8%80%20SDK/Python%20SDK.md)

[百度语音识别api](https://cloud.baidu.com/doc/SPEECH/s/Vk38lxily)

## others
[PaddleDetection目标检测训练项目数据集及其配置文件](https://aistudio.baidu.com/aistudio/projectdetail/646813)

[PaddleSeg道路分割数据集及其配置文件](https://aistudio.baidu.com/aistudio/projectdetail/626071)

