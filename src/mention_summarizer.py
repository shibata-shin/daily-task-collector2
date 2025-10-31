import os
from anthropic import Anthropic
from slack_client import SlackMentionClient


def summarize_mentions(mentions):
    """Claude APIを使ってメンションを要約"""
    if not mentions:
        return "過去24時間にメンションはありませんでした。"
    
    # メンション一覧をテキスト形式に整形
    mentions_text = ""
    for i, mention in enumerate(mentions, 1):
        mentions_text += f"\n--- メンション {i} ---\n"
        mentions_text += f"投稿者: {mention['user']}\n"
        mentions_text += f"チャンネル: #{mention['channel']}\n"
        mentions_text += f"内容: {mention['text']}\n"
        mentions_text += f"リンク: {mention['permalink']}\n"
    
    # Claude APIで要約
    # GitHub Actions環境でのプロキシ設定を無効化
    client = Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        default_headers={"anthropic-version": "2023-06-01"}
    )
    
    prompt = f"""以下は過去24時間にあなた宛に送られたSlackのメンション一覧です。
これらのメンションを以下の形式で要約してください：

1. **概要**：全体の傾向や重要なトピックを簡潔に
2. **重要なメンション**：特に対応が必要そうなものを優先順位順に
3. **カテゴリ別まとめ**：質問、依頼、情報共有などに分類

メンション一覧：
{mentions_text}

要約は読みやすく、アクションが必要な項目を明確にしてください。"""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    summary = message.content[0].text
    
    # メンション数を追加
    header = f"📬 *過去24時間のメンション要約* ({len(mentions)}件)\n\n"
    
    return header + summary


def main():
    print("Starting Slack mention summarizer...")
    
    # Slackクライアント初期化
    slack_client = SlackMentionClient()
    
    # メンション取得
    print("Fetching mentions...")
    mentions = slack_client.get_mentions_since_yesterday()
    print(f"Found {len(mentions)} mentions")
    
    # 要約生成
    print("Generating summary with Claude...")
    summary = summarize_mentions(mentions)
    
    # DM送信
    print("Sending DM...")
    slack_client.send_dm_to_self(summary)
    
    print("Process completed!")


if __name__ == "__main__":
    main()
