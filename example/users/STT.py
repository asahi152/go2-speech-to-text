import time
import sys
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize

import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import speech_recognition as sr
from pydub import AudioSegment
import subprocess
import os



STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理
def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

        else:
            data = json.loads(message)["data"]["result"]["ws"]
            # print(json.loads(message))
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            print("sid:%s call success!,data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))
    except Exception as e:
        print("receive msg,but parse exception:", e)



# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws,a,b):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:

                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


# 唤醒词处理
def wake_detection():
    # 这里调用科大讯飞的语音识别SDK文件进行唤醒词识别
    result = subprocess.run(["./awaken"])  
    if "MSP_IVW_MSG_WAKEUP" in result.stdout:
        return 1
    else: 
        return 0

#从系统麦克风拾取音频数据，采样率为 16000。能在用户结束说话时自动停止录制。
def rec(rate=16000):
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=rate) as source:
        print('正在获取声音中...')
        audio = r.listen(source)

    with open("recording.wav", "wb") as f:
        f.write(audio.get_wav_data())
        print('声音获取完成.')

    return 1

# 另一个录制函数，用来录制唤醒词音频
def rec_awake(rate=16000):
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=rate) as source:
        print('正在获取声音中...')
        audio = r.listen(source)

    with open("audio/awake.wav", "wb") as f:
        f.write(audio.get_wav_data())
        print('声音获取完成.')

    return 1

# 将录制得到的WAV格式文件转换为 PCM 格式
def convert_wav_to_pcm(wav_file, pcm_file):
    audio = AudioSegment.from_wav(wav_file)
    audio.export(pcm_file, format="raw")  # PCM 格式

if __name__ == "__main__":
    # sys.argv[1]: name of the network interface
    ChannelFactoryInitialize(0, sys.argv[1])   #初始化通道
    
    # 录制唤醒词音频
    rec_awake()
    wav_file = "audio/awake.wav"
    pcm_file = "audio/awake.pcm"
    convert_wav_to_pcm(wav_file,pcm_file)
    
    #将录制好的音频放入awaken.c指定的文件夹中 
    folder_path = '/home/byc/go2_sdk/unitree_sdk2_python/awaken/bin/auidio'
    file_name = 'audio/awake.pcm'
    file_path = os.path.join(folder_path, file_name)
    # 写入文件
    with open(file_path, 'w') as file:
        file.write('这是生成的内容。')

    print(f'文件已保存到: {file_path}')

    # 开始检测唤醒词
    flag = wake_detection()
    # 检测成功后开始录音并且调用语音听写API
    if flag == 1:       
        # 唤醒后开始录音
        rec()
        wav_file = "recording.wav"
        pcm_file = "output_audio.pcm"

        # 转换音频格式
        convert_wav_to_pcm(wav_file, pcm_file)

        # 测试时候在此处正确填写相关信息即可运行
        time1 = datetime.now()
        wsParam = Ws_Param(APPID='1b8f255d', APISecret='ZTNkMTcwYWU2ZWQyNGY2OTljYmE2OWY5',
                        APIKey='eae6e40b8cdf5a4836fdb8c4bf6301e9',
                        AudioFile=r'output_audio.pcm')
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        time2 = datetime.now()
        print(time2-time1)


