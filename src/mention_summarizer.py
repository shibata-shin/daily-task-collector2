import os
import httpx
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
    
    # プロキシを完全に無効化したHTTPクライアントを作成
    http_client = httpx.Client(
        proxies={},  # 空の辞書でプロキシを無効化
        transport=httpx.HTTPTransport(retries=3)
    )
    
    try:
        # Claude APIで要約
        client = Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            http_client=http_client
        )
        
        prompt = f"""以下は過去24時間にあなた宛に送られたSlackのメンション一覧です。
これらのメンションを以下の形式で要約してください：

【重要な指示】
- Slackで見やすいよう、シンプルな書式で出力してください
- **太字**は使わず、見出しに絵文字を使用してください
- メンションに言及する際は必ず「投稿者名（チャンネル名）」と「URL」を含めてください
- 箇条書きは「・」を使い、インデントで階層を表現してください

【要約の構成】
1. 📊 全体サマリー（1-2文で簡潔に）

2. 🔴 緊急対応が必要（優先度順、最大5件）
   各項目：投稿者（チャンネル）、内容の要点、URL

3. 🟡 重要だが緊急ではない（最大5件）
   各項目：投稿者（チャンネル）、内容の要点、URL

4. 📋 その他（カテゴリ別に簡潔に）
   ・質問・確認事項
   ・情報共有
   ・日程調整
   など

メンション一覧：
{mentions_text}

※出力例※
📊 全体サマリー
過去24時間で78件のメンションがありました。生成AI関連の運用ルール策定と経理関連の確認が急務です。

🔴 緊急対応が必要

• 生成AI API管理ルールの策定
  takasawa（pd-team）より
  API利用のクレカ申請フロー見直しが必要
  https://example.slack.com/...

• 委託販売契約書の提出
  tokita（経理）より  
  監査法人対応のため契約書提示が必要
  https://example.slack.com/...

🟡 重要だが緊急ではない

• 松本さんキックオフMTG日程調整
  営業チームより
  11/4 15:00～で調整中
  https://example.slack.com/...

📋 その他

質問・確認事項：
• 経理関連の確認3件
• 人事評価制度の質問2件

情報共有：
• AIマーケティングカンファレンス動画共有
• 座席配置変更のお知らせ"""
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        summary = message.content[0].text
        
        # メンション数を追加（シンプルなヘッダー）
        header = f"📬 過去24時間のメンション要約（{len(mentions)}件）\n\n"
        
        return header + summary
    
    except Exception as e:
        error_msg = str(e)
        if "credit balance is too low" in error_msg or "invalid_request_error" in error_msg:
            print(f"Anthropic API Error: {error_msg}")
            # クレジット不足の場合は簡易版の要約を返す
            header = f"📬 過去24時間のメンション一覧（{len(mentions)}件）\n"
            header += "⚠️ Anthropic APIのクレジット不足のため、リスト形式で表示\n\n"
            
            simple_summary = ""
            for i, mention in enumerate(mentions, 1):
                simple_summary += f"{i}. {mention['user']}（#{mention['channel']}）\n"
                simple_summary += f"   {mention['text'][:80]}...\n"
                simple_summary += f"   {mention['permalink']}\n\n"
            
            return header + simple_summary
        else:
            raise
    
    finally:
        # HTTPクライアントを閉じる
        http_client.close()


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
