"""
スクリーンショット自動撮影デスクトップアプリケーション

このモジュールは、指定された間隔で自動的にスクリーンショットを撮影するGUIアプリケーションを提供します。
重複検出機能、範囲選択機能、プログレス表示機能を含みます。
"""

import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Tuple, Any

from screenshot_module import ScreenshotCapture


class AppConfig:
    """アプリケーション設定定数クラス"""

    # ウィンドウ設定
    WINDOW_TITLE = "🌸スクリーンショット🌺"
    WINDOW_SIZE = "670x900"
    MIN_WINDOW_SIZE = (600, 700)

    # カラーテーマ（ナチュラルピンク×ベージュ/ブラウン）
    WARM_BEIGE = '#F5E6D3'      # メイン背景色 - 温かいベージュ
    SOFT_PINK = '#E8C2CA'       # アクセント色 - 落ち着いたピンク
    DUSTY_ROSE = '#D4A5A5'      # ホバー色 - くすんだローズ
    MAUVE_BROWN = '#C8999B'     # プレス色 - モーヴブラウン
    DEEP_BROWN = '#3D2E2A'      # テキスト色 - 深いブラウン
    CREAM_WHITE = '#FEFCF8'     # 入力フィールド背景 - クリーム白
    MUTED_GRAY = '#8B7B73'      # グレー系 - 落ち着いたグレー
    SAGE_GREEN = '#7A8471'      # 成功色 - セージグリーン
    RUST_RED = '#B5705C'        # エラー色 - ラストレッド

    # デフォルト値
    DEFAULT_SAVE_PATH = "./screenshots"
    DEFAULT_DURATION = 300
    DEFAULT_INTERVAL = 5
    DEFAULT_SIMILARITY = 95

    # UI設定
    MAIN_PADDING = "10"
    SECTION_PADDING = 8
    MAX_RECENT_ITEMS = 20
    PROGRESS_BAR_LENGTH = 400


class AppStyleManager:
    """アプリケーションスタイル管理クラス"""

    def __init__(self, root: tk.Tk):
        """
        スタイルマネージャーの初期化
        
        Args:
            root: メインウィンドウ
        """
        self.root = root
        self.style = ttk.Style()

    def setup_style(self) -> None:
        """アプリケーション全体のスタイルを設定"""
        self.style.theme_use('classic')
        self.root.configure(bg=AppConfig.WARM_BEIGE)

        self._configure_basic_styles()
        self._configure_button_styles()
        self._configure_custom_styles()

    def _configure_basic_styles(self) -> None:
        """基本的なウィジェットのスタイルを設定"""
        basic_styles = {
            'TFrame': {
                'background': AppConfig.WARM_BEIGE,
                'relief': 'flat',
                'borderwidth': 0
            },
            'TLabelFrame': {
                'background': AppConfig.WARM_BEIGE,
                'foreground': AppConfig.DEEP_BROWN,
                'relief': 'flat',
                'borderwidth': 1
            },
            'TLabelFrame.Label': {
                'background': AppConfig.WARM_BEIGE,
                'foreground': AppConfig.DEEP_BROWN
            },
            'TLabel': {
                'background': AppConfig.WARM_BEIGE,
                'foreground': AppConfig.DEEP_BROWN
            },
            'TEntry': {
                'background': AppConfig.CREAM_WHITE,
                'foreground': AppConfig.DEEP_BROWN,
                'fieldbackground': AppConfig.CREAM_WHITE,
                'borderwidth': 1
            },
            'TCombobox': {
                'background': AppConfig.CREAM_WHITE,
                'foreground': AppConfig.DEEP_BROWN,
                'fieldbackground': AppConfig.CREAM_WHITE,
                'borderwidth': 1
            },
            'TSpinbox': {
                'background': AppConfig.CREAM_WHITE,
                'foreground': AppConfig.DEEP_BROWN,
                'fieldbackground': AppConfig.CREAM_WHITE,
                'borderwidth': 1
            },
            'TProgressbar': {
                'background': AppConfig.SOFT_PINK,
                'troughcolor': AppConfig.WARM_BEIGE,
                'borderwidth': 0
            },
            'TScrollbar': {
                'background': AppConfig.SOFT_PINK,
                'troughcolor': AppConfig.WARM_BEIGE,
                'borderwidth': 0
            }
        }

        for style_name, config in basic_styles.items():
            self.style.configure(style_name, **config)

    def _configure_button_styles(self) -> None:
        """ボタンスタイルの設定"""
        self.style.configure('TButton',
                             background=AppConfig.SOFT_PINK,
                             foreground=AppConfig.DEEP_BROWN,
                             relief='raised',
                             borderwidth=1)

        # ボタンの状態別スタイル
        state_maps = {
            'TFrame': [('active', AppConfig.WARM_BEIGE), ('!active', AppConfig.WARM_BEIGE)],
            'TLabelFrame': [('active', AppConfig.WARM_BEIGE), ('!active', AppConfig.WARM_BEIGE)],
            'TLabelFrame.Label': [('active', AppConfig.WARM_BEIGE), ('!active', AppConfig.WARM_BEIGE)],
            'TLabel': [('active', AppConfig.WARM_BEIGE), ('!active', AppConfig.WARM_BEIGE)],
            'TButton': [
                ('active', AppConfig.DUSTY_ROSE),
                ('pressed', AppConfig.MAUVE_BROWN),
                ('!active', AppConfig.SOFT_PINK)
            ]
        }

        for style_name, state_map in state_maps.items():
            self.style.map(style_name, background=state_map)

    def _configure_custom_styles(self) -> None:
        """カスタムスタイルの設定"""
        custom_styles = {
            'Header.TLabel': {
                'font': ('Arial', 16, 'bold'),
                'background': AppConfig.WARM_BEIGE,
                'foreground': AppConfig.DEEP_BROWN
            },
            'Section.TLabel': {
                'font': ('Arial', 12, 'bold'),
                'background': AppConfig.WARM_BEIGE,
                'foreground': AppConfig.DEEP_BROWN
            },
            'Status.TLabel': {
                'font': ('Arial', 10),
                'background': AppConfig.WARM_BEIGE,
                'foreground': AppConfig.DEEP_BROWN
            }
        }

        for style_name, config in custom_styles.items():
            self.style.configure(style_name, **config)


class GUIBuilder:
    """GUI構築を担当するクラス"""

    def __init__(self, parent: tk.Widget, app_instance):
        """
        GUI構築クラスの初期化
        
        Args:
            parent: 親ウィジェット
            app_instance: メインアプリケーションインスタンス
        """
        self.parent = parent
        self.app = app_instance

    def create_scrollable_main_frame(self) -> ttk.Frame:
        """
        スクロール可能なメインフレームを作成
        
        Returns:
            メインフレーム
        """
        canvas = tk.Canvas(self.parent, bg=AppConfig.WARM_BEIGE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        self._setup_scrollable_events(canvas, scrollable_frame, scrollbar)
        self._pack_scrollable_widgets(canvas, scrollbar)

        main_frame = ttk.Frame(scrollable_frame, padding=AppConfig.MAIN_PADDING)
        main_frame.pack(fill="both", expand=True)

        return main_frame

    def _setup_scrollable_events(self, canvas: tk.Canvas,
                                 scrollable_frame: ttk.Frame,
                                 scrollbar: ttk.Scrollbar) -> None:
        """スクロール可能フレームのイベントを設定"""

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = event.width
            canvas.itemconfig(window_id, width=canvas_width)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scrollable_frame.bind("<Configure>", on_frame_configure)
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', on_canvas_configure)
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # 初期化完了後にCanvasサイズを調整
        self.parent.after(10, lambda: canvas.configure(scrollregion=canvas.bbox("all")))

    def _pack_scrollable_widgets(self, canvas: tk.Canvas, scrollbar: ttk.Scrollbar) -> None:
        """スクロール関連ウィジェットをパッキング"""
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

    def create_header_section(self, parent: ttk.Frame) -> None:
        """
        ヘッダーセクションを作成
        
        Args:
            parent: 親フレーム
        """
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))

        ttk.Label(header_frame, text=AppConfig.WINDOW_TITLE,
                  style='Header.TLabel').grid(row=0, column=0)

    def create_settings_section(self, parent: ttk.Frame) -> None:
        """
        設定セクションを作成
        
        Args:
            parent: 親フレーム
        """
        settings_frame = tk.LabelFrame(parent, text="🛒 設定",
                                       bg=AppConfig.WARM_BEIGE,
                                       fg=AppConfig.DEEP_BROWN,
                                       font=('Arial', 10),
                                       bd=1, relief='solid')
        settings_frame.configure(padx=AppConfig.SECTION_PADDING,
                                 pady=AppConfig.SECTION_PADDING)
        settings_frame.grid(row=1, column=0, columnspan=2, pady=(0, 8),
                            sticky=(tk.W, tk.E, tk.N))

        self._create_folder_settings(settings_frame)
        self._create_timing_settings(settings_frame)
        self._create_region_settings(settings_frame)
        self._create_similarity_settings(settings_frame)

        settings_frame.columnconfigure(0, weight=1)

    def _create_folder_settings(self, parent: tk.LabelFrame) -> None:
        """フォルダ設定UIを作成"""
        row = 0
        ttk.Label(parent, text="📁 保存先フォルダ:").grid(row=row, column=0, sticky=tk.W, pady=3)

        folder_frame = ttk.Frame(parent)
        folder_frame.grid(row=row + 1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=3)

        self.app.save_path_var = tk.StringVar(value=AppConfig.DEFAULT_SAVE_PATH)
        self.app.save_path_entry = ttk.Entry(folder_frame, textvariable=self.app.save_path_var, width=35)
        self.app.save_path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(folder_frame, text="📁 参照",
                   command=self.app.browse_folder).grid(row=0, column=1, padx=5)
        ttk.Button(folder_frame, text="✅ 確認",
                   command=self.app.validate_folder).grid(row=0, column=2, padx=5)

        folder_frame.columnconfigure(0, weight=1)

        # フォルダステータス
        self.app.folder_status_label = ttk.Label(parent, text="", foreground=AppConfig.SAGE_GREEN)
        self.app.folder_status_label.grid(row=row + 2, column=0, columnspan=3, sticky=tk.W, pady=3)

    def _create_timing_settings(self, parent: tk.LabelFrame) -> None:
        """タイミング設定UIを作成"""
        # 実行時間
        row = 3
        ttk.Label(parent, text="⏰ 実行時間 (秒):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.app.duration_var = tk.StringVar(value=str(AppConfig.DEFAULT_DURATION))
        duration_spin = ttk.Spinbox(parent, from_=1, to=3600,
                                    textvariable=self.app.duration_var, width=10)
        duration_spin.grid(row=row, column=1, sticky=tk.W, pady=3)

        # 撮影間隔
        row += 1
        ttk.Label(parent, text="⏱️ 撮影間隔 (秒):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.app.interval_var = tk.StringVar(value=str(AppConfig.DEFAULT_INTERVAL))
        interval_spin = ttk.Spinbox(parent, from_=1, to=60,
                                    textvariable=self.app.interval_var, width=10)
        interval_spin.grid(row=row, column=1, sticky=tk.W, pady=3)

    def _create_region_settings(self, parent: tk.LabelFrame) -> None:
        """撮影範囲設定UIを作成"""
        row = 5
        ttk.Label(parent, text="🔍 撮影範囲:").grid(row=row, column=0, sticky=tk.W, pady=3)

        region_frame = ttk.Frame(parent)
        region_frame.grid(row=row + 1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=3)

        ttk.Button(region_frame, text="🎯 範囲選択",
                   command=self.app.select_region).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(region_frame, text="🌐 全画面",
                   command=self.app.select_fullscreen).grid(row=0, column=1, padx=5)

        self.app.region_info_label = ttk.Label(region_frame, text="全画面")
        self.app.region_info_label.grid(row=0, column=2, sticky=tk.W, padx=10)

    def _create_similarity_settings(self, parent: tk.LabelFrame) -> None:
        """重複検出設定UIを作成"""
        row = 7
        ttk.Label(parent, text="🔄 重複検出閾値 (%):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.app.similarity_var = tk.StringVar(value=str(AppConfig.DEFAULT_SIMILARITY))
        similarity_spin = ttk.Spinbox(parent, from_=50, to=99,
                                      textvariable=self.app.similarity_var, width=10)
        similarity_spin.grid(row=row, column=1, sticky=tk.W, pady=3)

        ttk.Label(parent, text="この値以上に類似した画像は自動削除されます",
                  font=('Arial', 8), foreground=AppConfig.MUTED_GRAY).grid(
            row=row + 1, column=0, columnspan=3, sticky=tk.W, pady=2)

    def create_control_section(self, parent: ttk.Frame) -> None:
        """
        コントロールセクションを作成
        
        Args:
            parent: 親フレーム
        """
        control_frame = tk.LabelFrame(parent, text="🎮 実行コントロール",
                                      bg=AppConfig.WARM_BEIGE,
                                      fg=AppConfig.DEEP_BROWN,
                                      font=('Arial', 10),
                                      bd=1, relief='solid')
        control_frame.configure(padx=AppConfig.SECTION_PADDING,
                                pady=AppConfig.SECTION_PADDING)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(0, 8),
                           sticky=(tk.W, tk.E))

        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, pady=10)

        self.app.start_button = ttk.Button(button_frame, text="🚀 開始",
                                           command=self.app.start_capture,
                                           style='Accent.TButton')
        self.app.start_button.grid(row=0, column=0, padx=(0, 10))

        self.app.stop_button = ttk.Button(button_frame, text="🛑 停止",
                                          command=self.app.stop_capture,
                                          state=tk.DISABLED)
        self.app.stop_button.grid(row=0, column=1, padx=10)

    def create_status_section(self, parent: ttk.Frame) -> None:
        """
        ステータスセクションを作成
        
        Args:
            parent: 親フレーム
        """
        status_frame = tk.LabelFrame(parent, text="📊 撮影状況",
                                     bg=AppConfig.WARM_BEIGE,
                                     fg=AppConfig.DEEP_BROWN,
                                     font=('Arial', 10),
                                     bd=1, relief='solid')
        status_frame.configure(padx=AppConfig.SECTION_PADDING,
                               pady=AppConfig.SECTION_PADDING)
        status_frame.grid(row=3, column=0, columnspan=2, pady=(0, 8),
                          sticky=(tk.W, tk.E, tk.N, tk.S))

        self._create_status_info(status_frame)
        self._create_progress_bar(status_frame)
        self._create_recent_captures(status_frame)

        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(2, weight=1)

    def _create_status_info(self, parent: tk.LabelFrame) -> None:
        """ステータス情報UIを作成"""
        info_frame = ttk.Frame(parent)
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        status_items = [
            ("撮影状態:", "status_label", "待機中"),
            ("📷 撮影数:", "count_label", "0枚"),
            ("経過時間:", "elapsed_label", "0秒"),
            ("残り時間:", "remaining_label", "-")
        ]

        for i, (label_text, attr_name, default_value) in enumerate(status_items):
            ttk.Label(info_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, padx=(0, 10))
            label = ttk.Label(info_frame, text=default_value, style='Status.TLabel')
            label.grid(row=i, column=1, sticky=tk.W)
            setattr(self.app, attr_name, label)

    def _create_progress_bar(self, parent: tk.LabelFrame) -> None:
        """プログレスバーUIを作成"""
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.app.progress_var = tk.DoubleVar()
        self.app.progress_bar = ttk.Progressbar(progress_frame,
                                                variable=self.app.progress_var,
                                                length=AppConfig.PROGRESS_BAR_LENGTH,
                                                mode='determinate')
        self.app.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        self.app.progress_label = ttk.Label(progress_frame, text="0%")
        self.app.progress_label.grid(row=0, column=1)

        progress_frame.columnconfigure(0, weight=1)

    def _create_recent_captures(self, parent: tk.LabelFrame) -> None:
        """最新キャプチャ表示UIを作成"""
        recent_frame = tk.LabelFrame(parent, text="📷 最新のスクリーンショット",
                                     bg=AppConfig.WARM_BEIGE,
                                     fg=AppConfig.DEEP_BROWN,
                                     font=('Arial', 9),
                                     bd=1, relief='solid')
        recent_frame.configure(padx=5, pady=5)
        recent_frame.grid(row=2, column=0, columnspan=2,
                          sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        self.app.recent_listbox = tk.Listbox(recent_frame, height=6,
                                             bg=AppConfig.CREAM_WHITE,
                                             fg=AppConfig.DEEP_BROWN,
                                             selectbackground=AppConfig.SOFT_PINK)
        self.app.recent_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        recent_scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL,
                                         command=self.app.recent_listbox.yview)
        recent_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.app.recent_listbox.configure(yscrollcommand=recent_scrollbar.set)

        recent_frame.columnconfigure(0, weight=1)
        recent_frame.rowconfigure(0, weight=1)


class ScreenshotController:
    """スクリーンショット撮影制御クラス"""

    def __init__(self, app_instance):
        """
        撮影制御クラスの初期化
        
        Args:
            app_instance: メインアプリケーションインスタンス
        """
        self.app = app_instance
        self.screenshot_capture = ScreenshotCapture()
        self.is_capturing = False
        self.capture_thread: Optional[threading.Thread] = None
        self.selected_region: Optional[Tuple[int, int, int, int]] = None

    def select_region(self) -> None:
        """撮影範囲を選択"""
        try:
            # アプリウィンドウを最小化
            self.app.root.withdraw()
            self.app.root.update()
            time.sleep(0.2)

            self.selected_region = self.screenshot_capture.select_region()

            # ウィンドウを復元
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.root.focus_force()

            if self.selected_region:
                x, y, w, h = self.selected_region
                self.app.region_info_label.config(text=f"範囲: {x},{y} ({w}x{h})")
            else:
                self.app.region_info_label.config(text="範囲選択がキャンセルされました")

        except Exception as e:
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.root.focus_force()
            messagebox.showerror("エラー", f"範囲選択中にエラーが発生しました: {str(e)}")

    def select_fullscreen(self) -> None:
        """全画面撮影を選択"""
        self.selected_region = None
        self.app.region_info_label.config(text="全画面")

    def start_capture(self) -> None:
        """撮影を開始"""
        if self.is_capturing:
            messagebox.showwarning("警告", "キャプチャは既に実行中です")
            return

        if not self.app.validate_folder():
            return

        try:
            # パラメータの取得と設定
            self._setup_capture_parameters()
            self._update_ui_for_start()

            # キャプチャスレッド開始
            self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
            self.capture_thread.start()

        except ValueError:
            messagebox.showerror("エラー", "設定値が正しくありません")
        except Exception as e:
            messagebox.showerror("エラー", f"キャプチャ開始中にエラーが発生しました: {str(e)}")

    def _setup_capture_parameters(self) -> None:
        """撮影パラメータを設定"""
        save_path = self.app.save_path_var.get()
        duration = int(self.app.duration_var.get())
        interval = int(self.app.interval_var.get())
        similarity_threshold = int(self.app.similarity_var.get())

        self.screenshot_capture.setup(save_path, duration, interval,
                                      self.selected_region, similarity_threshold)

    def _update_ui_for_start(self) -> None:
        """撮影開始時のUI更新"""
        self.is_capturing = True
        self.app.start_button.config(state=tk.DISABLED)
        self.app.stop_button.config(state=tk.NORMAL)
        self.app.status_label.config(text="撮影中...")
        self.app.progress_var.set(0)
        
        # 最新のスクリーンショットリストをクリア
        self.app.recent_listbox.delete(0, tk.END)

    def stop_capture(self) -> None:
        """撮影を停止"""
        if not self.is_capturing:
            return

        self.is_capturing = False
        self.screenshot_capture.stop()

        # UI更新
        self.app.start_button.config(state=tk.NORMAL)
        self.app.stop_button.config(state=tk.DISABLED)
        self.app.status_label.config(text="停止中...")

    def _capture_worker(self) -> None:
        """バックグラウンド撮影処理"""
        start_time = time.time()
        count = 0
        duplicate_count = 0

        while self.is_capturing:
            try:
                # スクリーンショット取得
                result = self.screenshot_capture.capture()

                # 結果の処理
                filename, similarity = self._process_capture_result(result)

                # 経過時間の計算（撮影結果に関係なく常に実行）
                elapsed = time.time() - start_time
                remaining = self.screenshot_capture.duration - elapsed
                progress = (elapsed / self.screenshot_capture.duration) * 100

                if filename is None:
                    # 重複検出の場合
                    duplicate_count += 1
                    self.app.root.after(0, self.app.update_duplicate_status, similarity)
                    # 重複の場合でも時間情報を更新
                    self.app.root.after(0, self.app.update_time_info, int(elapsed), int(remaining), progress)
                else:
                    # 正常撮影の場合
                    count += 1
                    self.app.root.after(0, self.app.update_progress, count, int(elapsed),
                                        int(remaining), progress, filename)

                # 終了チェック
                if elapsed >= self.screenshot_capture.duration:
                    break

                time.sleep(self.screenshot_capture.interval)

            except Exception as e:
                self.app.root.after(0, self.app.show_error, str(e))
                break

        # 完了処理
        self.app.root.after(0, self.app.capture_complete, count, duplicate_count)

    def _process_capture_result(self, result: Any) -> Tuple[Optional[str], Optional[float]]:
        """
        撮影結果を処理
        
        Args:
            result: 撮影結果
            
        Returns:
            ファイル名と類似度のタプル
        """
        if isinstance(result, tuple):
            filename, similarity = result
            return filename, similarity
        else:
            return result, None


class ScreenshotApp:
    """メインアプリケーションクラス"""

    def __init__(self, root: tk.Tk):
        """
        アプリケーションの初期化
        
        Args:
            root: メインウィンドウ
        """
        self.root = root
        self._setup_window()

        # コンポーネントの初期化
        self.style_manager = AppStyleManager(root)
        self.style_manager.setup_style()

        self.controller = ScreenshotController(self)

        # GUI作成
        self._create_gui()

    def _setup_window(self) -> None:
        """ウィンドウの基本設定"""
        self.root.title(AppConfig.WINDOW_TITLE)
        self.root.geometry(AppConfig.WINDOW_SIZE)
        self.root.resizable(True, True)
        self.root.minsize(*AppConfig.MIN_WINDOW_SIZE)

    def _create_gui(self) -> None:
        """GUIを作成"""
        gui_builder = GUIBuilder(self.root, self)
        main_frame = gui_builder.create_scrollable_main_frame()

        # 各セクションの作成
        gui_builder.create_header_section(main_frame)
        gui_builder.create_settings_section(main_frame)
        gui_builder.create_control_section(main_frame)
        gui_builder.create_status_section(main_frame)

        # グリッドの重み設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def browse_folder(self) -> None:
        """フォルダ参照ダイアログを表示"""
        folder = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if folder:
            self.save_path_var.set(folder)
            self.validate_folder()

    def validate_folder(self) -> bool:
        """
        フォルダの有効性を検証
        
        Returns:
            フォルダが有効かどうか
        """
        folder_path = self.save_path_var.get()

        if not folder_path:
            self.folder_status_label.config(text="フォルダパスが入力されていません",
                                            foreground=AppConfig.RUST_RED)
            return False

        if os.path.exists(folder_path):
            if os.path.isdir(folder_path):
                self.folder_status_label.config(text="✅ フォルダが見つかりました",
                                                foreground=AppConfig.SAGE_GREEN)
                return True
            else:
                self.folder_status_label.config(text="指定されたパスはフォルダではありません",
                                                foreground=AppConfig.RUST_RED)
                return False
        else:
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.folder_status_label.config(text="✅ フォルダを作成しました",
                                                foreground=AppConfig.SAGE_GREEN)
                return True
            except Exception as e:
                self.folder_status_label.config(
                    text=f"フォルダの作成に失敗しました: {str(e)}",
                    foreground=AppConfig.RUST_RED)
                return False

    def select_region(self) -> None:
        """撮影範囲を選択"""
        self.controller.select_region()

    def select_fullscreen(self) -> None:
        """全画面撮影を選択"""
        self.controller.select_fullscreen()

    def start_capture(self) -> None:
        """撮影を開始"""
        # プライバシー警告の表示
        if not self._show_privacy_warning():
            return
        self.controller.start_capture()
        
    def _show_privacy_warning(self) -> bool:
        """プライバシー警告を表示"""
        warning_text = """⚠️ プライバシーとセキュリティに関する重要な警告 ⚠️

このアプリケーションは画面の内容を撮影・保存します。
以下の点にご注意ください：

🔴 撮影禁止対象:
• 個人情報（氏名、住所、電話番号等）
• 金融情報（口座番号、クレジットカード等）
• 企業の機密情報・顧客データ
• ログイン情報・パスワード画面
• 他人のプライベートな情報

⚖️ 法的注意事項:
• 各国の法律・規制を遵守してください
• 企業での使用は事前に許可を得てください
• 撮影による損害について開発者は責任を負いません

🛡️ セキュリティ注意:
• 画像は暗号化されずに保存されます
• 定期的に不要なファイルを削除してください

上記を理解し、責任を持って使用しますか？"""
        
        return messagebox.askyesno("プライバシー警告", warning_text)

    def stop_capture(self) -> None:
        """撮影を停止"""
        self.controller.stop_capture()

    def update_progress(self, count: int, elapsed: int, remaining: int,
                        progress: float, filename: str) -> None:
        """
        進捗を更新（メインスレッド）
        
        Args:
            count: 撮影数
            elapsed: 経過時間
            remaining: 残り時間
            progress: 進捗率
            filename: ファイル名
        """
        self.count_label.config(text=f"{count}枚")
        self.elapsed_label.config(text=f"{elapsed}秒")
        self.remaining_label.config(text=f"{remaining}秒")
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{progress:.1f}%")

        # 最新ファイルをリストに追加
        if filename:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.recent_listbox.insert(0, f"{timestamp} - {filename}")
            self._limit_recent_list()

    def update_duplicate_status(self, similarity: float) -> None:
        """
        重複検出ステータスを更新
        
        Args:
            similarity: 類似度
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.recent_listbox.insert(0, f"{timestamp} - 重複検出 (類似度: {similarity:.1f}%)")
        self._limit_recent_list()

    def update_time_info(self, elapsed: int, remaining: int, progress: float) -> None:
        """
        時間情報のみを更新（重複検出時用）
        
        Args:
            elapsed: 経過時間
            remaining: 残り時間
            progress: 進捗率
        """
        self.elapsed_label.config(text=f"{elapsed}秒")
        self.remaining_label.config(text=f"{remaining}秒")
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{progress:.1f}%")

    def _limit_recent_list(self) -> None:
        """最新リストの項目数を制限"""
        if self.recent_listbox.size() > AppConfig.MAX_RECENT_ITEMS:
            self.recent_listbox.delete(tk.END)

    def show_error(self, error_msg: str) -> None:
        """
        エラーを表示
        
        Args:
            error_msg: エラーメッセージ
        """
        messagebox.showerror("エラー", f"キャプチャ中にエラーが発生しました: {error_msg}")
        self.stop_capture()

    def capture_complete(self, total_count: int, duplicate_count: int) -> None:
        """
        撮影完了処理
        
        Args:
            total_count: 総撮影数
            duplicate_count: 重複数
        """
        self.controller.is_capturing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="完了")

        messagebox.showinfo("完了",
                            f"キャプチャが完了しました！\n"
                            f"撮影数: {total_count}枚\n"
                            f"重複削除: {duplicate_count}枚")


def main() -> None:
    """メイン関数"""
    root = tk.Tk()
    app = ScreenshotApp(root)

    def on_closing() -> None:
        """ウィンドウクローズ時の処理"""
        if app.controller.is_capturing:
            if messagebox.askokcancel("確認", "キャプチャ中です。終了しますか？"):
                app.stop_capture()
                time.sleep(0.5)  # 停止処理待ち
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
