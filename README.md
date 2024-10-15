# go2 语音转文字

## 功能特点

- 支持唤醒词检测。
- 可以将录制的音频转换为文本。
- 使用科大讯飞的语音识别 API。

## 环境要求

- Python 3.x
- 操作系统 Ubuntu20.04
- 相关库：
  - `websocket-client` - 用于 WebSocket 连接
  - `pydub` - 用于音频处理
  - `SpeechRecognition` - 用于语音识别
  - `unitree_sdk2py` - Unitree 机器人 SDK

## 安装依赖

手动安装以下依赖库：

```bash
pip install websocket-client pydub SpeechRecognition
```

## 使用方法

1. **克隆仓库**

   ```bash
   git clone https://github.com/asahi152/go2-speech-to-text.git
   cd go2-speech-to-text
   ```

2. **编译唤醒词 SDK**

 在运行代码时，awaken.c 文件会自动编译。确保相关的编译工具（gcc）已安装在系统中。

3. **运行程序**

   执行主程序：

   ```bash
   python3 STT.py <网络接口名>
   ```

  本项目录音生成的wav文件会自动转化为pcm文件储存在根目录，唤醒词awaken.pcm会复制到./awaken/bin/audio文件夹中等待处理，确保该文件夹存在。

  唤醒词资源存放在 ./awaken/bin/msc/res文件夹，设定为“开始识别”。
