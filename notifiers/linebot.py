#Notifier for NAVER Line bot
from  notifiers.baseNotifier import Job, BaseNotifier

from linebot import (
    LineBotApi
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)



#Push messages to NAVER line chat
class LineBotNotifier(BaseNotifier):
    __channelAccessToken = ""
    __line_bot_api = None
    __targetId = ""

    #Channel access token you will find on the Line API developer site, the target is your user ID "U1234567..."
    def __init__(self, channelAccessToken, targetID) -> None:
        super().__init__()
        self.__channelAccessToken = channelAccessToken
        self.__line_bot_api = LineBotApi(self.__channelAccessToken)
        self.__targetId = targetID



    #---------------------------------------------------------------------------------------------------------
    def NotifyServerReady(self):
        try:
            #see https://developers.line.biz/en/docs/messaging-api/emoji-list/#specify-emojis-in-message-object
            #and https://pypi.org/project/line-bot-sdk/
            emoji = [
                {
                    "index": 0,
                    "productId": "5ac21a18040ab15980c9b43e",
                    "emojiId": "029" #a fire
                }
            ]
            self.__line_bot_api.push_message(self.__targetId , TextSendMessage(text="$ " + self._makeReadyMsg(), emojis=emoji))
        except Exception as ex:
            print(f"LineBotNotifier.ready failed with message '{ str(ex)}'")



    #---------------------------------------------------------------------------------------------------------
    def NotifyJobStart(self, j: Job):
        try:
            #see https://developers.line.biz/en/docs/messaging-api/emoji-list/#specify-emojis-in-message-object
            #and https://pypi.org/project/line-bot-sdk/
            emoji = [
                {
                    "index": 0,
                    "productId": "5ac21a18040ab15980c9b43e",
                    "emojiId": "217" #a star like thing
                }
            ]
            self.__line_bot_api.push_message(self.__targetId , TextSendMessage(text="$ " + self._makeStartMsg(j), emojis=emoji))
        except Exception as ex:
            print(f"LineBotNotifier.start failed with message '{ str(ex)}'")




    #---------------------------------------------------------------------------------------------------------
    def NotifyJobCompletion(self, j: Job):
        try:
            #see https://developers.line.biz/en/docs/messaging-api/emoji-list/#specify-emojis-in-message-object
            #and https://pypi.org/project/line-bot-sdk/
            emoji = [
                {
                    "index": 0,
                    "productId": "5ac21a18040ab15980c9b43e",
                    "emojiId": "007" #a big checkmark blue
                }
            ]            
            self.__line_bot_api.push_message(self.__targetId , TextSendMessage(text="$ " + self._makeCompletionMsg(j), emojis=emoji))
        except Exception as ex:
            print(f"LineBotNotifier.complete failed with message '{ str(ex)}'")




    #---------------------------------------------------------------------------------------------------------
    def NotifyJobError(self, j: Job, extra:str = None):
        try:
            #see https://developers.line.biz/en/docs/messaging-api/emoji-list/#specify-emojis-in-message-object
            #and https://pypi.org/project/line-bot-sdk/
            emoji = [
                {
                    "index": 0,
                    "productId": "5ac21a18040ab15980c9b43e",
                    "emojiId": "059" #a skull
                }
            ]            
            self.__line_bot_api.push_message(self.__targetId , TextSendMessage(text="$ " + self._makeErrorMsg(j, extra=extra), emojis=emoji))
        except Exception as ex:
            print(f"LineBotNotifier.error failed with message '{ str(ex)}'")
