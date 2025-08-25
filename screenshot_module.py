"""
スクリーンショット自動取得モジュール

このモジュールは、指定された間隔でスクリーンショットを自動取得し、
重複画像の検出・削除機能を提供します。
"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import Optional, Tuple, List

import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageTk
from skimage.metrics import structural_similarity as ssim

# 定数定義
DEFAULT_DURATION = 60  # デフォルト実行時間（秒）
DEFAULT_INTERVAL = 5  # デフォルト間隔（秒）
DEFAULT_SIMILARITY_THRESHOLD = 95  # デフォルト類似度閾値（%）
MIN_REGION_SIZE = 1  # 最小領域サイズ（ピクセル）


class ScreenshotCapture:
    """
    スクリーンショット自動取得クラス
    
    指定された設定に基づいてスクリーンショットを自動取得し、
    重複画像の検出・削除を行います。
    
    Attributes:
        save_path (Optional[str]): 保存先ディレクトリパス
        duration (int): 実行時間（秒）
        interval (int): キャプチャ間隔（秒）
        region (Optional[List[int]]): キャプチャ領域 [x, y, width, height]
        is_running (bool): 実行状態フラグ
        similarity_threshold (int): 重複判定の類似度閾値（%）
        last_screenshot_path (Optional[str]): 前回のスクリーンショットパス
    """

    def __init__(self) -> None:
        """
        ScreenshotCaptureクラスのコンストラクタ
        
        初期値でインスタンス変数を設定します。
        """
        self.save_path: Optional[str] = None
        self.duration: int = DEFAULT_DURATION
        self.interval: int = DEFAULT_INTERVAL
        self.region: Optional[List[int]] = None
        self.is_running: bool = False
        self.similarity_threshold: int = DEFAULT_SIMILARITY_THRESHOLD
        self.last_screenshot_path: Optional[str] = None

    def setup(self,
              save_path: str,
              duration: int,
              interval: int,
              region: Optional[List[int]] = None,
              similarity_threshold: int = DEFAULT_SIMILARITY_THRESHOLD) -> None:
        """
        キャプチャ設定を行います
        
        Args:
            save_path (str): スクリーンショット保存先ディレクトリパス
            duration (int): 実行時間（秒）
            interval (int): キャプチャ間隔（秒）
            region (Optional[List[int]]): キャプチャ領域 [x, y, width, height]
            similarity_threshold (int): 重複判定の類似度閾値（%）
        """
        self.save_path = save_path
        self.duration = duration
        self.interval = interval
        self.region = region
        self.similarity_threshold = similarity_threshold
        self.last_screenshot_path = None

    def capture(self) -> Tuple[Optional[str], Optional[float]]:
        """
        スクリーンショットを取得します
        
        設定された領域（または全画面）のスクリーンショットを取得し、
        前回の画像との類似度を比較して重複を検出します。
        
        Returns:
            Tuple[Optional[str], Optional[float]]: 
                - ファイル名（重複時はNone）
                - 類似度（重複でない場合はNone）
                
        Raises:
            Exception: スクリーンショット取得に失敗した場合
        """
        try:
            # タイムスタンプ付きファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.save_path, filename)

            # スクリーンショット取得
            screenshot = self._take_screenshot()
            screenshot.save(filepath)

        except Exception as e:
            print(f"スクリーンショット取得エラー: {e}")
            raise Exception(f"スクリーンショット取得に失敗しました: {str(e)}")

        # 重複検出処理
        return self._check_and_handle_duplicate(filename, filepath)

    def _take_screenshot(self) -> Image.Image:
        """
        実際のスクリーンショット取得を行います
        
        Returns:
            Image.Image: 取得したスクリーンショット画像
        """
        if self.region:
            # 指定範囲のスクリーンショット
            validated_region = self._validate_region(self.region)
            screenshot = pyautogui.screenshot(region=validated_region)
        else:
            # 全画面スクリーンショット
            screenshot = pyautogui.screenshot()

        return screenshot

    def _validate_region(self, region: List[int]) -> Tuple[int, int, int, int]:
        """
        キャプチャ領域の妥当性を検証し、修正します
        
        Args:
            region (List[int]): 検証する領域 [x, y, width, height]
            
        Returns:
            Tuple[int, int, int, int]: 修正された領域 (x, y, width, height)
        """
        x, y, width, height = region

        # 画面サイズを取得
        screen_size = pyautogui.size()
        screen_width, screen_height = screen_size.width, screen_size.height

        # 境界チェックと修正
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))

        # 幅と高さの修正
        max_width = screen_width - x
        max_height = screen_height - y
        width = max(MIN_REGION_SIZE, min(width, max_width))
        height = max(MIN_REGION_SIZE, min(height, max_height))

        return (x, y, width, height)

    def _check_and_handle_duplicate(self, filename: str, filepath: str) -> Tuple[Optional[str], Optional[float]]:
        """
        重複画像の検出と処理を行います
        
        Args:
            filename (str): 新しいファイル名
            filepath (str): 新しいファイルパス
            
        Returns:
            Tuple[Optional[str], Optional[float]]: ファイル名と類似度
        """
        if self.last_screenshot_path and os.path.exists(self.last_screenshot_path):
            similarity = self.calculate_similarity(self.last_screenshot_path, filepath)

            if similarity >= self.similarity_threshold:
                # 重複として削除
                os.remove(filepath)
                return None, similarity  # 削除されたことを示すためにNoneを返す

        self.last_screenshot_path = filepath
        return filename, None

    def calculate_similarity(self, image1_path: str, image2_path: str) -> float:
        """
        2つの画像の類似度を計算します（構造的類似性指数を使用）
        
        Args:
            image1_path (str): 比較する画像1のパス
            image2_path (str): 比較する画像2のパス
            
        Returns:
            float: 類似度（0-100の範囲）
        """
        try:
            # 画像を読み込み
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)

            if img1 is None or img2 is None:
                return 0.0

            # グレースケールに変換
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # 画像サイズを統一
            gray1, gray2 = self._resize_images_to_match(gray1, gray2)

            # 構造的類似性指数（SSIM）を計算
            similarity_index = ssim(gray1, gray2)

            # パーセンテージに変換
            return similarity_index * 100

        except Exception as e:
            print(f"類似度計算エラー: {e}")
            return 0.0

    def _resize_images_to_match(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        2つの画像のサイズを統一します
        
        Args:
            img1 (np.ndarray): 画像1
            img2 (np.ndarray): 画像2
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: サイズ統一後の画像ペア
        """
        if img1.shape != img2.shape:
            # より小さいサイズに合わせる
            h = min(img1.shape[0], img2.shape[0])
            w = min(img1.shape[1], img2.shape[1])
            img1 = cv2.resize(img1, (w, h))
            img2 = cv2.resize(img2, (w, h))

        return img1, img2

    def calculate_histogram_similarity(self, image1_path: str, image2_path: str) -> float:
        """
        ヒストグラム比較による類似度計算（バックアップメソッド）
        
        Args:
            image1_path (str): 比較する画像1のパス
            image2_path (str): 比較する画像2のパス
            
        Returns:
            float: 類似度（0-100の範囲）
        """
        try:
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)

            if img1 is None or img2 is None:
                return 0.0

            # HSV色空間に変換
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

            # ヒストグラムを計算
            hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
            hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])

            # 相関係数で比較
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

            return correlation * 100

        except Exception as e:
            print(f"ヒストグラム類似度計算エラー: {e}")
            return 0.0

    def stop(self) -> None:
        """キャプチャを停止します"""
        self.is_running = False

    def select_region(self) -> Optional[List[int]]:
        """
        範囲選択GUIを表示します
        
        Returns:
            Optional[List[int]]: 選択された領域 [x, y, width, height]、
                               キャンセルされた場合はNone
        """
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを隠す

        try:
            region_selector = RegionSelector()
            region = region_selector.select_region()
            return region
        finally:
            root.destroy()


class RegionSelector:
    """
    画面範囲選択用のGUIクラス
    
    全画面オーバーレイを表示し、マウスドラッグによる範囲選択機能を提供します。
    
    Attributes:
        start_x (Optional[int]): ドラッグ開始X座標
        start_y (Optional[int]): ドラッグ開始Y座標
        end_x (Optional[int]): ドラッグ終了X座標
        end_y (Optional[int]): ドラッグ終了Y座標
        rect (Optional[int]): 選択矩形のキャンバスオブジェクト
        canvas (Optional[tk.Canvas]): 描画用キャンバス
        root (Optional[tk.Toplevel]): メインウィンドウ
    """

    def __init__(self) -> None:
        """RegionSelectorクラスのコンストラクタ"""
        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None
        self.end_x: Optional[int] = None
        self.end_y: Optional[int] = None
        self.rect: Optional[int] = None
        self.canvas: Optional[tk.Canvas] = None
        self.root: Optional[tk.Toplevel] = None

    def select_region(self) -> Optional[List[int]]:
        """
        範囲選択ダイアログを表示し、ユーザーの選択を取得します
        
        Returns:
            Optional[List[int]]: 選択された領域 [x, y, width, height]、
                               キャンセルされた場合はNone
                               
        Raises:
            Exception: 範囲選択の初期化に失敗した場合
        """
        try:
            # 全画面スクリーンショットを取得
            screenshot = pyautogui.screenshot()

            # 全画面ウィンドウを作成
            self._create_fullscreen_window()

            # スクリーンショットをキャンバスに表示
            self._setup_canvas_with_screenshot(screenshot)

            # イベントハンドラーを設定
            self._setup_event_handlers()

            # 説明ラベルを追加
            self._add_instruction_label()

            # フォーカスを設定してモーダル表示
            self.root.focus_set()
            self.root.wait_window()

            # 選択結果を計算して返す
            return self._calculate_selected_region()

        except Exception as e:
            print(f"範囲選択初期化エラー: {e}")
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
            raise Exception(f"範囲選択の初期化に失敗しました: {str(e)}")

    def _create_fullscreen_window(self) -> None:
        """全画面ウィンドウを作成します"""
        self.root = tk.Toplevel()
        self.root.title("範囲選択 - ドラッグして選択してください")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')

    def _setup_canvas_with_screenshot(self, screenshot: Image.Image) -> None:
        """スクリーンショットをキャンバスに設定します"""
        # キャンバスを作成
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 画像をキャンバスに表示（参照を属性に保持してGCを防止）
        screen_width = screenshot.width
        screen_height = screenshot.height

        self.photo = ImageTk.PhotoImage(screenshot)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # 選択用の半透明オーバーレイ
        self.overlay_rect_id = self.canvas.create_rectangle(
            0, 0, screen_width, screen_height,
            fill='black', stipple='gray50', outline=''  # stippleで透過風に見せる
        )

    def _setup_event_handlers(self) -> None:
        """イベントハンドラーを設定します"""
        # マウスイベント
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)

        # キーボードイベント
        self.root.bind('<Escape>', lambda e: self.cancel_selection())
        self.root.bind('<Return>', lambda e: self.confirm_selection())

    def _add_instruction_label(self) -> None:
        """操作説明ラベルを追加します"""
        label = tk.Label(
            self.root,
            text="ドラッグして範囲を選択してください (Enter: 確定, Escape: キャンセル)",
            bg='yellow',
            fg='black',
            font=('Arial', 12)
        )
        label.pack(pady=10)

    def _calculate_selected_region(self) -> Optional[List[int]]:
        """選択された領域を計算します"""
        if not all([self.start_x is not None, self.start_y is not None,
                    self.end_x is not None, self.end_y is not None]):
            return None

        # 範囲計算
        x = min(self.start_x, self.end_x)
        y = min(self.start_y, self.end_y)
        width = abs(self.end_x - self.start_x)
        height = abs(self.end_y - self.start_y)

        # 最小サイズの保証
        width = max(MIN_REGION_SIZE, width)
        height = max(MIN_REGION_SIZE, height)

        # 画面サイズ内に調整
        return self._adjust_region_to_screen(x, y, width, height)

    def _adjust_region_to_screen(self, x: int, y: int, width: int, height: int) -> List[int]:
        """領域を画面サイズ内に調整します"""
        # 画面サイズを取得
        screen_size = pyautogui.size()
        screen_width, screen_height = screen_size.width, screen_size.height

        # 境界内に収める
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))

        # 幅と高さを画面サイズ内に調整
        if x + width > screen_width:
            width = screen_width - x
        if y + height > screen_height:
            height = screen_height - y

        return [x, y, width, height]

    def on_click(self, event: tk.Event) -> None:
        """
        マウスクリック時のイベントハンドラー
        
        Args:
            event (tk.Event): マウスクリックイベント
        """
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event: tk.Event) -> None:
        """
        マウスドラッグ時のイベントハンドラー
        
        Args:
            event (tk.Event): マウスドラッグイベント
        """
        if self.start_x is not None and self.start_y is not None:
            # 既存の矩形を削除
            if self.rect:
                self.canvas.delete(self.rect)

            # 新しい選択矩形を描画
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2, fill='', dash=(5, 5)
            )

    def on_release(self, event: tk.Event) -> None:
        """
        マウスリリース時のイベントハンドラー
        
        Args:
            event (tk.Event): マウスリリースイベント
        """
        self.end_x = event.x
        self.end_y = event.y

    def cancel_selection(self) -> None:
        """選択をキャンセルします"""
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.root.destroy()

    def confirm_selection(self) -> None:
        """
        選択を確定します
        
        有効な選択がない場合は警告を表示します。
        """
        if all([self.start_x is not None, self.start_y is not None,
                self.end_x is not None, self.end_y is not None]):
            self.root.destroy()
        else:
            messagebox.showwarning("警告", "範囲を選択してください")


# pyautoguiのフェイルセーフを有効のまま維持（安全性のため）
# マウスを画面の左上角(0,0)に移動すると緊急停止可能
# pyautogui.FAILSAFE = False  # セキュリティ上の理由で無効化を削除
