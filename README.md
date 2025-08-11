# 🌺 スクリーンショット自動撮影アプリ 🌸

指定された間隔で自動的にスクリーンショットを撮影するデスクトップアプリケーションです。

## ✨ 主な機能

- 🕒 **自動撮影**: 指定した間隔で継続的にスクリーンショットを撮影
- 🎯 **範囲選択**: 撮影範囲を自由に選択可能
- 🔄 **重複検出**: 類似した画像を自動的に検出・削除
- 📊 **進捗表示**: リアルタイムで撮影状況を表示

## 📁 プロジェクト構成

```
screenshot/
├── desktop_app.py          # メインアプリケーション
├── screenshot_module.py    # スクリーンショット撮影機能
├── requirements.txt        # 依存関係
├── README.md              # このファイル
├── .gitignore             # Git除外設定
├── .venv/                 # 仮想環境（自動生成）
└── screenshots/           # 撮影画像保存フォルダ（自動生成）
```

## 🚀 セットアップ

### 1. リポジトリのクローンまたはダウンロード

```bash
# Gitでクローンする場合
git clone <repository-url>
cd screenshot

# または手動でファイルをダウンロード
```

### 2. 仮想環境の作成と有効化

```bash
# 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
# Windows (PowerShell)
.\.venv\Scripts\activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

### 3. 依存関係のインストール

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt

# pipのアップグレード（推奨）
python -m pip install --upgrade pip
```

### 4. アプリケーションの起動

```bash
# アプリケーションを実行
python desktop_app.py
```

## 🛠️ 依存ライブラリ

- **Pillow**: 画像処理ライブラリ
- **pyautogui**: スクリーンショット撮影自動化
- **opencv-python**: コンピュータビジョンと画像処理
- **numpy**: 数値計算
- **scikit-image**: 構造的類似性指数(SSIM)計算

## 📖 使用方法

1. **保存先フォルダの設定**: 撮影したスクリーンショットの保存先を指定
2. **撮影設定**: 実行時間と撮影間隔を設定
3. **撮影範囲の選択**: 全画面または特定の範囲を選択
4. **重複検出閾値の設定**: 類似画像の検出感度を調整
5. **撮影開始**: 開始ボタンをクリックして撮影を開始

## 🎯 重複検出機能

- **構造的類似性指数(SSIM)**: 画像の構造的な類似性を評価
- **ヒストグラム比較**: 色分布の類似性を評価
- **自動削除**: 設定した閾値以上の類似画像を自動削除

## 🔧 設定項目

| 項目 | 説明 | 範囲 |
|------|------|------|
| 実行時間 | 撮影を継続する時間（秒） | 1-3600 |
| 撮影間隔 | スクリーンショットの撮影間隔（秒） | 1-60 |
| 重複検出閾値 | 類似画像として判定する閾値（%） | 50-99 |

## 🏗️ アーキテクチャ

アプリケーションは以下のクラスで構成されています：

- **AppConfig**: 設定定数管理
- **AppStyleManager**: UIスタイル管理
- **GUIBuilder**: GUI構築
- **ScreenshotController**: 撮影制御
- **ScreenshotApp**: メインアプリケーション

## 🐛 トラブルシューティング

### scikit-image関連のエラー

```bash
# ModuleNotFoundError: No module named 'skimage'
pip install scikit-image
```

### pyautogui関連のエラー

```bash
# Windowsの場合
pip install pyautogui --upgrade

# macOSの場合、アクセシビリティ許可が必要
```

### OpenCV関連のエラー

```bash
pip install opencv-python --upgrade
```

### 仮想環境が認識されない場合

```bash
# 仮想環境の再作成
python -m venv .venv --clear
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 文字エンコーディングエラー

Windowsで日本語文字のエラーが発生する場合は、UTF-8エンコーディングを使用してください。

## 🔄 開発

### 新しい依存関係の追加

```bash
# パッケージをインストール
pip install <package-name>

# requirements.txtを更新
pip freeze > requirements.txt
```

### Git管理

このプロジェクトには`.gitignore`ファイルが含まれており、以下が自動的に除外されます：
- 仮想環境ディレクトリ (`.venv/`)
- 生成された画像ファイル (`screenshots/`)
- Pythonキャッシュファイル (`__pycache__/`)
- IDE設定ファイル

