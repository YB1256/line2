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
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

app = Flask(__name__)

# 填入你的 Channel Secret 與 Channel Access Token
CHANNEL_SECRET = 'c76bbb88883763a8a5e3dd36e25600c3'
CHANNEL_ACCESS_TOKEN = 'AkgR2cdGZ5NPue3rZA6lDu7iaSy/kNTZaqdtA6UwHyBpfsKmPFi5jqweK5aUXF1qYkFEdMqp6XIqVOJzSqLjH9mWtDluLnkRI1RfVG+Bc7yjdS925LCxwUhJajvNgsnsWig5IV2NvxWcyup3O322ygdB04t89/1O/w1cDnyilFU='

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 接收 LINE 傳送過來的 Webhook 請求
@app.route("/callback", methods=['POST'])
def callback():
    # 取得 LINE 的數位簽章
    signature = request.headers['X-Line-Signature']
    # 取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證數位簽章並處理請求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Check your channel secret/access token.")
        abort(400)
    return 'OK'

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 使用 ApiClient 與 MessagingApi 來回覆訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 將使用者傳來的文字，原封不動回傳 (Echo)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )

if __name__ == "__main__":
    # 本地端測試時，啟動在 5000 port
    app.run(port=5000)
