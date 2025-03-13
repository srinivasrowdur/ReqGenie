"""
Utility functions for supporting multiple languages.
"""

def get_language_instruction(language):
    """Generate language-specific instructions for agents.
    
    Args:
        language: The selected language (English, Japanese, or Italian)
        
    Returns:
        Instructions to include with agent prompts
    """
    if language == "English":
        return "Generate all content in English."
    elif language == "Japanese":
        return """
        すべてのコンテンツを日本語で生成してください。
        レスポンスは完全に日本語で、専門用語も日本語で適切に翻訳してください。
        要件、テストケース、ユースケース、コードコメントなどすべての出力を日本語で作成してください。
        """
    elif language == "Italian":
        return """
        Genera tutti i contenuti in italiano.
        La risposta deve essere completamente in italiano, con i termini tecnici tradotti appropriatamente.
        Produci tutti gli output in italiano, inclusi requisiti, casi di test, casi d'uso e commenti al codice.
        """
    else:
        return "Generate all content in English."

def get_ui_text(key, language):
    """Get UI text in the selected language.
    
    Args:
        key: The text identifier
        language: The selected language
        
    Returns:
        The localized text
    """
    texts = {
        "analyzing": {
            "English": "Analyzing",
            "Japanese": "分析中",
            "Italian": "Analizzando"
        },
        "enter_requirement": {
            "English": "Enter your requirement:",
            "Japanese": "要件を入力してください:",
            "Italian": "Inserisci il tuo requisito:"
        },
        "requirement_placeholder": {
            "English": "Example: Create a secure login screen with email and password authentication, including input validation and error handling.",
            "Japanese": "例: メールとパスワードによる認証、入力検証、エラー処理を含む安全なログイン画面を作成する。",
            "Italian": "Esempio: Crea una schermata di login sicura con autenticazione tramite email e password, inclusa la convalida dell'input e la gestione degli errori."
        },
        "download_requirements": {
            "English": "Download Requirements Document",
            "Japanese": "要件ドキュメントをダウンロード",
            "Italian": "Scarica Documento dei Requisiti"
        },
        "download_usecases": {
            "English": "Download Use Cases",
            "Japanese": "ユースケースをダウンロード",
            "Italian": "Scarica Casi d'Uso"
        },
        "download_testcases": {
            "English": "Download Test Cases",
            "Japanese": "テストケースをダウンロード",
            "Italian": "Scarica Casi di Test"
        },
        "download_code": {
            "English": "Download Sample Code",
            "Japanese": "サンプルコードをダウンロード",
            "Italian": "Scarica Codice di Esempio"
        }
    }
    
    # Return the text in the selected language, or English as fallback
    return texts.get(key, {}).get(language, texts.get(key, {}).get("English", key)) 