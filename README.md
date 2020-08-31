# Ar_project
本人参加2020全国大学生物联网设计大赛所做项目负责的软件部分，获得华东赛区特等奖、全国总决赛二等奖。
    该项目包含了导航系统、语音系统、目标检测系统三个部分，涵盖语音唤醒、语音识别、语音合成、语音导航、目的地搜索、路径规划、车道分割、目标检测(车、车牌、违规车、路标等)、车牌识别等一整套快速解决方案！

# 项目技术架构如下图
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/%E6%95%B4%E4%BD%93%E6%A1%86%E6%9E%B6.png)

# 目录结构
```c
Project
├─AR_project_PI
│  │  ARPImain.py //主程序
│  │  ARui.py //界面类
│  │  Arrowclass.py //箭头类
│  │  construction.png
│  │  cv2test.py
│  │  foundgreen.mp4
│  │  foundred.mp4
│  │  get_AndroidGps_server.py //从app获取输入的目的地gps信息
│  │  GPStransformer.py 
│  │  height_limit.png
│  │  MPU6050filter.py
│  │  MPU6065reader.py //陀螺仪传感器数据读取,需要自行矫正
│  │  Navigation_system.py //导航系统类
│  │  picameratest.py
│  │  pi_clientcv.py //摄像头数据获取与处理
│  │  resources_rc.py //图标资源
│  │  resources_rc.qrc
│  │  webBrowser.py //内嵌浏览器
│  │  webtest.py 
│  │  
│  ├─arrow //箭头图片文件夹
│  │      forward.png
│  │      forward2.png
│  │      left.png
│  │      right.png
│  │      
│  ├─Navigationhtml //预设html文件夹
│  │      initpage.html
│  │      keywordsearch.html
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
│      │  demo.py
│      │  lxyysbtest.py
│      │  Makefile
│      │  snowboy-detect-swig.cc
│      │  snowboy-detect-swig.i
│      │  snowboy-detect-swig.o
│      │  snowboydecoder.py
│      │  snowboydetect.py
│      │  test.py
│      │  text2voice.py 
│      │  txpythonsdk.py //腾讯sdk改写的语音合成,需要补充自己的apikey
│      │  voicecontroller.py //语音控制系统基类,汇总了语音唤醒,语音识别,语音合成类等
│      │  voice_and_text.py //文字语音相互转换基类
│      │  _snowboydetect.so
│      │  关闭投影.pmdl
│      │  打开投影.pmdl
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
        仿射变换test.py //仿射变换测试
        初始化服务端的json路径.py //以下如名
        标注好的图片更改大小.py
        标注好的图片重命名.py
        生成文件名列表.py
        移除不存在文件.py
        透视变换test.py
        随机分数据集.py
        随机重命名.py
```
所有关键类的注释都已经打上了，自己慢慢看...各个模块可以单独运行测试
# 实际画面

## 关于投影画面
投影我们采用的是dlp2000充当树莓派的屏幕直接显示，然后在树莓派上运行窗口程序即产生投影Ar效果。有关，dlp模块与树莓派连接可以看这个https://blog.csdn.net/qq_25160559/article/details/106062176
使用树莓派4B需要改一下分辨率，不然会有画面倾斜等，参考https://e2e.ti.com/support/dlp/f/94/t/850392?DLPDLCR2000EVM-Resolution-problem-settings-with-i2c-and-raspberry-pi
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200826_200301.jpg)
## 投影效果
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200823_205618.jpg)
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200827_180415.jpg)
![image](https://github.com/fandesfyf/Ar_project/blob/master/pic/IMG_20200831_162918.jpg)


