import os
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackMentionClient:
    def __init__(self):
        # User Tokenのみを使用
        self.client = WebClient(token=os.environ["SLACK_USER_TOKEN"])
        self.user_id = os.environ["SLACK_USER_ID"]
    
    def get_mentions_since_yesterday(self):
        """過去24時間の自分宛メンションを取得"""
        try:
            # 24時間前のタイムスタンプを計算
            yesterday = datetime.now() - timedelta(days=1)
            query = f"<@{self.user_id}> after:{yesterday.strftime('%Y-%m-%d')}"
            
            # search.messages APIで検索
            result = self.client.search_messages(
                query=query,
                sort="timestamp",
                sort_dir="desc",
                count=100
            )
            
            if not result["ok"]:
                print(f"Error searching messages: {result}")
                return []
            
            matches = result.get("messages", {}).get("matches", [])
            
            # メッセージ情報を整形
            mentions = []
            for match in matches:
                mention_data = {
                    "text": match["text"],
                    "user": match.get("username", "Unknown"),
                    "channel": match.get("channel", {}).get("name", "Unknown"),
                    "timestamp": match["ts"],
                    "permalink": match.get("permalink", "")
                }
                mentions.append(mention_data)
            
            return mentions
        
        except SlackApiError as e:
            print(f"Error fetching mentions: {e.response['error']}")
            return []
    
    def send_dm_to_self(self, message):
        """自分宛にDMを送信（User Tokenで実行）"""
        try:
            # im.openで自分とのDMチャンネルを開く
            response = self.client.conversations_open(users=[self.user_id])
            channel_id = response["channel"]["id"]
            
            # メッセージを送信
            self.client.chat_postMessage(
                channel=channel_id,
                text=message,
                unfurl_links=False,
                unfurl_media=False
            )
            
            print("DM sent successfully")
            return True
        
        except SlackApiError as e:
            print(f"Error sending DM: {e.response['error']}")
            return False
