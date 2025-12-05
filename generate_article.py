# ----------------------------------------------------------------------
# 🚨 最終最終最終修正: venv内を再帰的に検索してsite-packagesを強制特定 🚨
# GitHub Actions環境で発生するModuleNotFoundErrorを解決するためのコード
import sys
import os
import glob
import re

# スクリプトのベースディレクトリ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PATH = os.path.join(BASE_DIR, 'venv')

# venvディレクトリ内の 'site-packages' フォルダをワイルドカードで検索
site_packages_candidates = glob.glob(os.path.join(VENV_PATH, '**', 'site-packages'), recursive=True)

found_path = None
# 候補の中から、libまたはlib64以下にあるパスを選定
for path in site_packages_candidates:
    if 'venv' in path and re.search(r'(lib|lib64)/python\d\.\d/site-packages', path):
        found_path = path
        break

# 見つかったパスをPythonの検索パス(sys.path)に追加
if found_path and found_path not in sys.path:
    sys.path.append(found_path)
    # print(f"✅ 強制 PYTHONPATH に {found_path} を追加しました。")

# ----------------------------------------------------------------------
# 以下、モジュールのインポート
import json
import re
from datetime import datetime
# 💡 パス設定が成功していれば、ここでインポートが成功します 💡
import google.generativeai as genai 

# --- 1. 定数と初期設定 ---

# 🚨 ここは公開サイトのURLに合わせてください 🚨
BASE_URL = "https://kiruha0315-debug.github.io/" 

# 生成する記事の基本設定
TARGET_KEYWORD = "2026年のAI技術トレンドとビジネスへの応用"
SEARCH_INTENT = "具体的なトレンドと、企業が今すぐ取り組むべき戦略を知りたい"

# --- 2. Gemini APIの設定 ---

def configure_api():
    """Gemini APIキーを設定する"""
    API_KEY = os.environ.get("GEMINI_API_KEY") 
    
    if not API_KEY:
        print("エラー: GEMINI_API_KEYが環境変数に設定されていません。")
        return False
    
    genai.configure(api_key=API_KEY)
    print("✅ Gemini API設定完了。")
    return True

def get_gemini_response(prompt, json_mode=False):
    """Gemini APIを呼び出す共通関数"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        config = {}
        if json_mode:
            config["response_mime_type"] = "application/json"
        
        response = model.generate_content(prompt, generation_config=config)
        
        if json_mode:
            # JSONモードの場合、{}で囲まれた部分を抽出
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        
        return response.text
    except Exception as e:
        print(f"🚨 AI処理中にエラーが発生しました: {e}")
        return None

# --- 3. 記事生成ロジック ---

def generate_outline_and_body():
    """骨子と本文を一括で生成する"""
    print(f"🤖 キーワード: {TARGET_KEYWORD} の記事生成を開始します...")
    
    full_prompt = f"""
    あなたはプロのSEOライターです。以下のキーワードと検索意図に基づき、SEOで上位表示を目指す記事全体をJSON形式で生成してください。
    【キーワード】: {TARGET_KEYWORD}
    【検索意図】: {SEARCH_INTENT}
    
    【ルール】
    1.  記事の本文は合計2000文字以上とし、網羅性を高めてください。
    2.  H2, H3見出しを使って本文を構造化し、Markdown形式で記述してください。
    
    【出力形式】
    {{
        "title": "記事のSEOタイトル (35文字以内)",
        "meta_description": "記事のメタディスクリプション (120文字以内)",
        "body_markdown": "## 導入\n本文...\n## 2026年の主要トレンド\n本文...\n"
    }}
    """
    
    data = get_gemini_response(full_prompt, json_mode=True)
    
    if data and data.get("body_markdown"):
        print("✅ 記事本文とメタ情報の生成が完了しました。")
        return data
    else:
        print("❌ 記事生成に失敗しました。")
        return None

# --- 4. HTML出力とファイル保存 ---

def create_and_save_html(article_data):
    """記事データをHTMLファイルとして保存する"""
    
    body_markdown = article_data["body_markdown"]
    title = article_data["title"]
    meta_description = article_data["meta_description"]
    
    # Markdownを簡単なHTMLに変換 (簡易的な置換)
    body_html = body_markdown.replace('## ', '<h2>').replace('### ', '<h3>')
    body_html = body_html.replace('\n\n', '</p><p>')
    body_html = re.sub(r'<h2>(.*?)', r'</p><h2>\1', body_html)
    body_html = re.sub(r'<h3>(.*?)', r'</p><h3>\1', body_html)
    body_html = f"<p>{body_html}</p>"

    # ファイル名と公開URLのパスを生成
    today_str = datetime.now().strftime("%Y%m%d")
    url_slug = re.sub(r'[^a-z0-9]+', '-', TARGET_KEYWORD.lower()).strip('-')[:30]
    filename = f"{today_str}-{url_slug}.html"
    
    # AdSenseコードはダミーを使用 
    ADSENSE_CODE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2130894810041111" crossorigin="anonymous"></script>'
    
    # GSC確認タグ
    GSC_VERIFICATION = '<meta name="google-site-verification" content="gQHkk6TWzD6wsQHRbbQt5o8yszlMxyKs3LgeqAzOyg4" />'

    html_template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_description}">
    {GSC_VERIFICATION}
    {ADSENSE_CODE}
    <style>
        body {{ font-family: 'Yu Gothic', 'Meiryo', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        p {{ margin-bottom: 1em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>公開日: {today_str}</p>
    {body_html}
    
    <div style="height: 100px; background-color: #f0f0f0; margin-top: 30px; text-align: center; line-height: 100px;">[広告枠]</div>

</body>
</html>
"""
    
    # ファイルとして保存
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"💾 記事をファイル '{filename}' として保存しました。")
    return filename

# --- メイン処理 ---

def main():
    if configure_api():
        article_data = generate_outline_and_body()
        if article_data:
            create_and_save_html(article_data)

if __name__ == "__main__":
    main()
