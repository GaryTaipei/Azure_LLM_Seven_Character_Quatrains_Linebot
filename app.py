import sys
import configparser

# Azure Speech
import azure.cognitiveservices.speech as speechsdk #pip install azure-cognitiveservices-speech
import librosa #pip install librosa

# Azure OpenAI
import os
from openai import AzureOpenAI #pip install openai

from flask import Flask, request, abort #pip install Flask
from linebot.v3 import WebhookHandler #pip install line-bot-sdk
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
) 
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    AudioMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)


# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

# Azure Speech Settings
speech_config = speechsdk.SpeechConfig(
    subscription=config["AzureSpeech"]["SPEECH_KEY"],
    region=config["AzureSpeech"]["SPEECH_REGION"],
)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
UPLOAD_FOLDER = "static"

# Azure OpenAI Key
client = AzureOpenAI(
    api_key=config["AzureOpenAI"]["KEY"],
    api_version=config["AzureOpenAI"]["VERSION"],
    azure_endpoint=config["AzureOpenAI"]["BASE"],
)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

channel_access_token = config["Line"]["CHANNEL_ACCESS_TOKEN"]
channel_secret = config["Line"]["CHANNEL_SECRET"]
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

handler = WebhookHandler(channel_secret) 
configuration = Configuration(access_token=channel_access_token)

openai_result_cache = []

#搭配 Linbot Message Channel 小綱故事創造館
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    match event.message.text.lower():
        case "cheerful":
            if len(openai_result_cache) > 0:
                azure_openai_result = openai_result_cache[-1]
                print("cache:",azure_openai_result)
                audio_duration = azure_speech(azure_openai_result,voice_style="cheerful",target_language="zh-Hant")
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            AudioMessage(
                                originalContentUrl=f"{config['Deploy']['CURRENT_WEBSITE']}/static/outputaudio.wav",
                                duration=audio_duration,
                            ),
                        ],
                    )
                )
        case "sorry":
            if len(openai_result_cache) > 0:
                azure_openai_result = openai_result_cache[-1]
                print("cache:",azure_openai_result)
                audio_duration = azure_speech(azure_openai_result,voice_style="sorry",target_language="zh-Hant")
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            AudioMessage(
                                originalContentUrl=f"{config['Deploy']['CURRENT_WEBSITE']}/static/outputaudio.wav",
                                duration=audio_duration,
                            ),
                        ],
                    )
                )
        case "empathetic":
            if len(openai_result_cache) > 0:
                azure_openai_result = openai_result_cache[-1]
                print("cache:",azure_openai_result)
                audio_duration = azure_speech(azure_openai_result,voice_style="empathetic",target_language="zh-Hant")
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            AudioMessage(
                                originalContentUrl=f"{config['Deploy']['CURRENT_WEBSITE']}/static/outputaudio.wav",
                                duration=audio_duration,
                            ),
                        ],
                    )
                )
        case _:
            azure_openai_result = azure_openai(event.message.text)
            openai_result_cache.append(azure_openai_result) #將 openai 回覆的結果存入快取
            audio_duration = azure_speech(azure_openai_result)
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=azure_openai_result),
                            TextMessage(text='請從下列選項中選擇一個你想聽的語音的語調',
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyItem(action=MessageAction(label="快樂", text="Cheerful")),
                                        QuickReplyItem(action=MessageAction(label="悲傷", text="Sorry")),
                                        QuickReplyItem(action=MessageAction(label="同情", text="Empathetic")),
                                    ]
                                )
                            ),
                        ],
                    )
                )
            



    # azure_openai_result = azure_openai(event.message.text)
    # openai_result_cache.append(azure_openai_result) #將 openai 回覆的結果存入快取
    # audio_duration = azure_speech(azure_openai_result)
    # with ApiClient(configuration) as api_client:
    #     line_bot_api = MessagingApi(api_client)
    #     line_bot_api.reply_message_with_http_info(
    #         ReplyMessageRequest(
    #             reply_token=event.reply_token,
    #             messages=[
    #                 TextMessage(text=azure_openai_result),
    #                 TextMessage(text='請從下列選項中選擇一個你想聽的語音的語調',
    #                     quick_reply=QuickReply(
    #                         items=[
    #                             #QuickReplyItem(action=PostbackAction(label="label1", data="data1")),
    #                             QuickReplyItem(action=MessageAction(label="Cheerful", text="Cheerful")),
    #                             #QuickReplyItem(action=DatetimePickerAction(label="label3",data="data3",mode="date")),
    #                             #QuickReplyItem(action=CameraAction(label="label4")),
    #                             #QuickReplyItem(action=CameraRollAction(label="label5")),
    #                             #QuickReplyItem(action=LocationAction(label="label6")),
    #                         ]
    #                     )
    #                 ),
    #                 # AudioMessage(
    #                 #     originalContentUrl=f"{config['Deploy']['CURRENT_WEBSITE']}/static/outputaudio.wav",
    #                 #     duration=audio_duration,
    #                 # ),
    #             ],
                
    #         )
    #     )

def azure_openai(user_input):
    role_description = """
    你是一個國學大師，你擅長寫七言絕句，內容平仄對丈，符合押韻規則，用詞華麗。
    """
    custom_user_input = ""
    custom_user_input += "請用這個關鍵字「"
    custom_user_input += user_input
    custom_user_input += "」創作一首七言絕句。"
    message_text = [
        {
            "role": "system",
            "content": role_description,
        },
        {"role": "user", "content": user_input},
    ]

    completion = client.chat.completions.create(
        model=config["AzureOpenAI"]["DEPLOYMENT_NAME"],
        messages=message_text,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )
    print(completion)
    return completion.choices[0].message.content

def azure_speech(openai_output,voice_style="cheerful",target_language="zh-Hant"):
    role_dic = {
        "zh-Hant": "zh-CN-XiaoxiaoMultilingualNeural",
        "ja": "ja-JP-NanamiNeural",
    }

    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name = role_dic[target_language] #"zh-CN-XiaoxiaoMultilingualNeural"
    file_name = "outputaudio.wav"
    file_config = speechsdk.audio.AudioOutputConfig(filename="static/" + file_name)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=file_config
    )

    print("voice_style:",voice_style)
    print("target_language:",target_language)
    print("voice_name:",role_dic[target_language])
    # Receives a text from console input and synthesizes it to wave file.
    # result = speech_synthesizer.speak_text_async(openai_output).get()

    ssml_input = ""
    ssml_input += f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{role_dic[target_language][:5]}">'
    ssml_input += f'<voice name="{role_dic[target_language]}">'
    ssml_input += f'<mstts:express-as style="{voice_style}" styledegree="6">'
    ssml_input += openai_output
    ssml_input += "</mstts:express-as>"
    ssml_input += "</voice>"
    ssml_input += "</speak>"
    result = speech_synthesizer.speak_ssml_async(ssml_input).get()

    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(
            "Speech synthesized for text [{}], and the audio was saved to [{}]".format(
                openai_output, file_name
            )
        )
        audio_duration = round(
            librosa.get_duration(path="static/outputaudio.wav") * 1000
        )
        print(audio_duration)
        return audio_duration

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))


if __name__ == "__main__":
    app.run()