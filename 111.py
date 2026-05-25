from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# ================= 請確實填入你的 LINE 憑證 =================
CHANNEL_ACCESS_TOKEN = 'nvEidaWDbptgZDRFkg/En2SEhQnL2S1meTmZQm5YpLPkyshhjmgCX3MXvpRlvDf+Zfljrd/vZzkNLM+sB3V61n yuhkyPE6DRs32mfWSbWatWKfedWCqfWUxbrmSmDH2/rr5paPSkM3Iw2rOY9jkbxgdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'edaa32c5f521236e2f91656f145c4f93'
# =========================================================

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 核心路由：確保名稱跟 methods 完全正確
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("憑證驗證失敗，請檢查 Token 或 Secret 是否填錯！")
        abort(400)

    return 'OK'

# 當收到 LINE 文字訊息時觸發
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    print(f"收到使用者訊息: {user_message}") # 讓你在 cmd 看到測試狀況
   
    if user_message == "你好":
        reply_text = "你好，我是黃韻安的機器人"
       
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)