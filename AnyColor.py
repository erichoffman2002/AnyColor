import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QLabel, QSlider, QFileDialog, QFrame, QCheckBox, QTextEdit, QInputDialog, QComboBox, QTabWidget, QListWidget, QGridLayout, QGroupBox, QToolTip, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage, QPainter, QLinearGradient, QColor, QFont
from PIL import Image, ImageQt, ImageFilter
import numpy as np
import colorsys
import math
from Styles import *  # Import all styles
from ImageEffects import (
    adjust_pixel, apply_color_option, apply_glow_effect, 
    save_image_with_transparency, get_gradient_colors, 
    adjust_image_size, adjust_size_for_glow
)

# Global constants
COLOR_TOLERANCE = 2  # Tolerance for background color detection

# Define option_descriptions with appropriate descriptions for each option
option_descriptions = {
    "None": "No effect applied.",
    "Negative": "Inverts the colors of the image.",
    "Greyscale": "Converts the image to greyscale.",
    "Neon Outburst": "Enhances saturation and brightness for a neon effect.",
    "Cyber Glow": "Adds a glow effect with a slight hue shift.",
    "Aurora Prism": "Applies a gradient hue shift across the image.",
    "Chromatic Fragment": "Reduces saturation and applies a slight hue shift.",
    "Vibrant Spectrum": "Increases saturation for a vibrant look.",
    "Mystic Mirage": "Reduces saturation and increases brightness.",
    "Holographic Shift": "Applies a vertical gradient hue shift.",
    "Quantum Leap": "Inverts colors for a dramatic effect.",
    "Psychedelic Cascade": "Applies a diagonal gradient hue shift.",
    "Digital Overdrive": "Enhances brightness significantly.",
    "Earth Tones": "Adds a warm tint and reduces saturation.",
    "Pastel Palette": "Reduces saturation and increases brightness for a pastel look."
}

class EffectListWidget(QListWidget):
    """Widget to display all applied effects"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(LIST_WIDGET_STYLE)
        self.setWordWrap(True)
        
    def update_effects(self, effects_dict):
        """Update the list of applied effects"""
        self.clear()
        for category, effects in effects_dict.items():
            if effects:  # Only add category if it has effects
                self.addItem(f"=== {category} ===")
                for effect in effects:
                    self.addItem(f"  • {effect}")

class HueGradientBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        # Add color stops for a full hue rotation
        for i in range(7):
            hue = i / 6
            color = QColor.fromHsvF(hue, 1.0, 1.0)
            gradient.setColorAt(i / 6, color)
        # Add the first color again at the end to complete the cycle
        gradient.setColorAt(1, QColor.fromHsvF(0, 1.0, 1.0))
        painter.fillRect(self.rect(), gradient)


class ColorBalanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Color Balance")
        self.resize(1200, 800)
        
        # Use a better window state that respects the taskbar
        # Don't use WindowMaximized as it's causing geometry issues
        self.setWindowFlags(Qt.WindowType.Window)
        
        # Wait until after show() to maximize
        # This will be applied in showEvent method
        self._should_maximize = True
        
        # Define the effects lists first
        self.available_effects = [
            "None", "Negative", "Greyscale", "Neon Outburst",
            "Cyber Glow", "Aurora Prism", "Chromatic Fragment",
            "Vibrant Spectrum", "Mystic Mirage", "Holographic Shift",
            "Quantum Leap", "Psychedelic Cascade", "Digital Overdrive",
            "Earth Tones", "Pastel Palette"
        ] 
        self.available_glow_effects = [
            "None", "Blue Glow", "Red Glow", "Green Glow",
            "Blue Border", "Red Border", "Green Border", "Rainbow Border"
        ]
        
        # Initialize current effects
        self.current_effect = "None"
        self.current_glow = "None"
        self.current_directory = ""
        self.current_image_index = 0
        self.image_files = []
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create left panel with fixed width based on percentage of screen width
        left_panel = QWidget()
        screen_width = self.screen().size().width()
        left_panel_width = int(screen_width * 0.25)  # Reduced from 0.3 to 0.25
        left_panel.setFixedWidth(left_panel_width)
        left_panel.setMaximumWidth(left_panel_width)  # Additional constraint
        layout.addWidget(left_panel)  # Remove stretch factor
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        left_layout.setSpacing(5)  # Reduce spacing
        # Create all buttons and controls first
        button_font = QFont()
        button_font.setPointSize(button_font.pointSize() + 1)
        # Create top buttons section
        top_buttons = QWidget()
        top_layout = QVBoxLayout(top_buttons)
        # Load Directory button
        self.load_button = QPushButton("Load Directory")
        self.load_button.setFont(button_font)
        self.load_button.clicked.connect(self.load_directory)
        
        # Create horizontal layout for load buttons
        load_buttons_layout = QHBoxLayout()
        load_buttons_layout.addWidget(self.load_button)
        
        # Add view directory button with eye icon
        self.view_directory_button = QPushButton("👁️")
        self.view_directory_button.setToolTip("Open directory in Explorer (second monitor)")
        self.view_directory_button.setFixedWidth(30)
        self.view_directory_button.setStyleSheet(VIEW_DIRECTORY_BUTTON_STYLE)
        self.view_directory_button.clicked.connect(self.open_directory_explorer)
        load_buttons_layout.addWidget(self.view_directory_button)
        
        top_layout.addLayout(load_buttons_layout)
        # Directory display label
        self.directory_label = QLabel()
        self.directory_label.setFont(button_font)
        self.directory_label.setWordWrap(True)
        self.directory_label.setStyleSheet(DIRECTORY_LABEL_STYLE)
        font = self.directory_label.font()
        font.setPointSize(font.pointSize() + 2)
        self.directory_label.setFont(font)
        top_layout.addWidget(self.directory_label)
        # Add top buttons to left layout
        left_layout.addWidget(top_buttons)
        # Create sliders
        self.sliders = {}
        self.slider_labels = {}  # Store labels for reference if needed
        for label_text, key in [
            ("Cyan-Red", "cyan_red"),
            ("Magenta-Green", "magenta_green"),
            ("Yellow-Blue", "yellow_blue")
        ]:
            label, slider = self.create_slider(label_text, key)
            self.slider_labels[key] = label  # Store label if needed later
        
        # Create hue controls with fixed height
        self.hue_label = QLabel("Hue Rotation")
        self.hue_label.setFont(button_font)
        self.hue_label.setFixedHeight(20)  # Fix height
        self.hue_gradient = HueGradientBar()
        self.hue_gradient.setFixedHeight(10)  # Fix height
        self.sliders["hue"] = QSlider(Qt.Orientation.Horizontal)
        self.sliders["hue"].setFixedHeight(20)  # Fix height
        self.sliders["hue"].setMinimum(-180)
        self.sliders["hue"].setMaximum(180)
        self.sliders["hue"].setValue(0)
        self.sliders["hue"].sliderReleased.connect(self.apply_adjustments)
        
        # Create tab style with smaller font
        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_STYLE)
        
        # Add fixed maximum height to prevent expansion
        tabs.setMaximumHeight(300)
        tabs.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        # Create and setup tabs
        color_tab = QWidget()
        color_tab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        effects_tab = QWidget()
        effects_tab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        glow_tab = QWidget()
        glow_tab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        color_layout = QVBoxLayout(color_tab)
        color_layout.setContentsMargins(5, 5, 5, 5)
        color_layout.setSpacing(2)  # Reduce spacing even further
        
        effects_layout = QVBoxLayout(effects_tab)
        effects_layout.setContentsMargins(5, 5, 5, 5)
        
        glow_layout = QVBoxLayout(glow_tab)
        glow_layout.setContentsMargins(5, 5, 5, 5)
        
        # Color Adjustments Tab - Fixed heights for all sliders and labels
        color_controls = QWidget()
        color_controls.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        color_controls_layout = QVBoxLayout(color_controls)
        color_controls_layout.setContentsMargins(0, 0, 0, 0)
        color_controls_layout.setSpacing(2)
        
        for label_text in ["Cyan-Red", "Magenta-Green", "Yellow-Blue"]:
            label = QLabel(label_text)
            label.setFixedHeight(20)
            color_controls_layout.addWidget(label)
            slider = self.sliders[label_text.lower().replace("-", "_")]
            slider.setFixedHeight(20)
            color_controls_layout.addWidget(slider)
            
        # Hue rotation section
        hue_controls = QWidget()
        hue_controls.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        hue_layout = QVBoxLayout(hue_controls)
        hue_layout.setContentsMargins(0, 0, 0, 0)
        hue_layout.setSpacing(2)
        
        hue_layout.addWidget(self.hue_label)
        hue_layout.addWidget(self.hue_gradient)
        hue_layout.addWidget(self.sliders["hue"])
        
        color_layout.addWidget(color_controls)
        color_layout.addWidget(hue_controls)
        color_layout.addStretch(1)  # Add stretch to prevent expansion
        
        # Special Effects Tab - Replace dropdown with buttons
        effects_grid = QGridLayout()
        effects_layout.addLayout(effects_grid)
        # Enable mouse tracking for the entire effects tab
        effects_tab.setMouseTracking(True)
        # Create effect buttons in two columns
        for i, effect in enumerate(self.available_effects):
            btn = QPushButton(effect)
            btn.setFont(button_font)
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            if effect == "None":
                btn.setChecked(True)
            # Just set the tooltip text directly from option_descriptions
            if effect in option_descriptions:
                btn.setToolTip(option_descriptions[effect])
            btn.clicked.connect(lambda checked, e=effect: self.select_effect(e))
            effects_grid.addWidget(btn, i // 2, i % 2)

        # Glow/Border Tab Layout
        # Width control with label and slider on same line
        width_layout = QHBoxLayout()
        width_layout.setSpacing(5)
        glow_layout.addLayout(width_layout)
        width_label = QLabel("Effect Width:")
        width_label.setFixedHeight(25)
        width_layout.addWidget(width_label)
        self.width_value_label = QLabel("5")
        self.width_value_label.setFixedSize(30, 25)
        self.width_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.width_value_label.setStyleSheet(WIDTH_VALUE_LABEL_STYLE)
        width_layout.addWidget(self.width_value_label)
        self.border_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.border_width_slider.setFixedHeight(25)
        self.border_width_slider.setMinimum(2)
        self.border_width_slider.setMaximum(30)
        self.border_width_slider.setValue(5)
        self.border_width_slider.valueChanged.connect(self.update_width_label)
        width_layout.addWidget(self.border_width_slider)
        # Gradient Controls
        gradient_group = QGroupBox("Color Options")
        gradient_group.setStyleSheet(GRADIENT_GROUP_STYLE)
        gradient_layout = QVBoxLayout(gradient_group)
        glow_layout.addWidget(gradient_group)

        # Mode Selection
        mode_layout = QHBoxLayout()
        self.single_color_mode = QCheckBox("Double Color Mode")
        self.single_color_mode.stateChanged.connect(self.toggle_color_mode)
        mode_layout.addWidget(self.single_color_mode)
        gradient_layout.addLayout(mode_layout)

        # Color Selection
        colors_layout = QVBoxLayout()  # Changed from QHBoxLayout to QVBoxLayout
        gradient_layout.addLayout(colors_layout)
        
        # Start Color
        start_layout = QHBoxLayout()
        colors_layout.addLayout(start_layout)
        
        # Label and preview in one layout
        label_preview = QHBoxLayout()
        self.start_color_label = QLabel("Color:")
        label_preview.addWidget(self.start_color_label)
        
        self.start_color_preview = QLabel()
        self.start_color_preview.setFixedSize(50, 20)
        self.start_color_preview.setStyleSheet(COLOR_PREVIEW_STYLE)
        label_preview.addWidget(self.start_color_preview)
        start_layout.addLayout(label_preview)
        
        # Slider and its gradient in a vertical layout
        slider_layout = QVBoxLayout()
        self.start_color_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_color_slider.setMinimum(0)
        self.start_color_slider.setMaximum(359)
        self.start_color_slider.setValue(240)
        self.start_color_slider.valueChanged.connect(lambda: self.update_color_preview("start"))
        slider_layout.addWidget(self.start_color_slider)

        # Add color gradient bar directly under slider
        self.start_gradient_bar = HueGradientBar()
        self.start_gradient_bar.setFixedHeight(10)
        slider_layout.addWidget(self.start_gradient_bar)
        slider_layout.setSpacing(2)  # Reduce space between slider and gradient
        
        start_layout.addLayout(slider_layout)

        # End Color
        self.end_color_container = QWidget()
        self.end_color_container.setVisible(False)
        end_layout = QVBoxLayout(self.end_color_container)
        
        end_color_row = QHBoxLayout()
        end_layout.addLayout(end_color_row)
        
        end_color_row.addWidget(QLabel("End Color:"))
        self.end_color_preview = QLabel()
        self.end_color_preview.setFixedSize(50, 20)
        self.end_color_preview.setStyleSheet(COLOR_PREVIEW_STYLE)
        end_color_row.addWidget(self.end_color_preview)
        
        self.end_color_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_color_slider.setMinimum(0)
        self.end_color_slider.setMaximum(359)
        self.end_color_slider.setValue(0)
        self.end_color_slider.valueChanged.connect(lambda: self.update_color_preview("end"))
        end_color_row.addWidget(self.end_color_slider)

        # Add color gradient bar under end slider
        self.end_gradient_bar = HueGradientBar()
        self.end_gradient_bar.setFixedHeight(10)
        end_layout.addWidget(self.end_gradient_bar)
        
        colors_layout.addWidget(self.end_color_container)

        # Gradient Type (hidden by default)
        self.gradient_container = QWidget()
        self.gradient_container.setVisible(False)
        gradient_controls = QVBoxLayout(self.gradient_container)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Gradient Type:"))
        self.gradient_type = QComboBox()
        self.gradient_type.addItems(["Linear", "Radial", "Angular"])
        self.gradient_type.currentTextChanged.connect(self.update_gradient)
        gradient_controls.addLayout(type_layout)

        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        self.gradient_direction = QComboBox()
        self.gradient_direction.addItems(["Horizontal", "Vertical", "Diagonal ↘", "Diagonal ↗"])
        self.gradient_direction.currentTextChanged.connect(self.update_gradient)
        gradient_controls.addLayout(direction_layout)
        
        gradient_layout.addWidget(self.gradient_container)

        # Effect Buttons
        button_layout = QHBoxLayout()
        glow_layout.addLayout(button_layout)
        
        # Enable mouse tracking for the glow tab
        glow_tab.setMouseTracking(True)
        
        # Add None button first
        self.none_glow_button = QPushButton("None")
        self.none_glow_button.setCheckable(True)
        self.none_glow_button.setChecked(True)
        self.none_glow_button.setToolTip("Remove glow/border effect")
        self.none_glow_button.setMouseTracking(True)
        self.none_glow_button.clicked.connect(lambda: self.handle_glow_click("None"))
        button_layout.addWidget(self.none_glow_button)
        
        self.glow_button = QPushButton("Apply Color Glow")
        self.glow_button.setCheckable(True)
        self.glow_button.setToolTip("Applies a soft colored glow around the edges")
        self.glow_button.setMouseTracking(True)
        self.glow_button.clicked.connect(lambda: self.handle_glow_click("glow"))
        
        self.border_button = QPushButton("Apply Color Border")
        self.border_button.setCheckable(True)
        self.border_button.setToolTip("Applies a solid colored border around the edges")
        self.border_button.setMouseTracking(True)
        self.border_button.clicked.connect(lambda: self.handle_glow_click("border"))
        
        button_layout.addWidget(self.glow_button)
        button_layout.addWidget(self.border_button)
        
        # Add tabs
        tabs.addTab(color_tab, "Color Adjustments")
        tabs.addTab(effects_tab, "Special Effects")
        tabs.addTab(glow_tab, "Glow/Border")
        
        # Add tabs to left layout
        left_layout.addWidget(tabs)
        
        # Add Applied Effects List with smaller height
        effects_label = QLabel("Applied Effects:")
        effects_label.setFont(button_font)
        left_layout.addWidget(effects_label)
        
        self.effects_list = EffectListWidget()
        self.effects_list.setMaximumHeight(120)  # Increased height for effects list
        left_layout.addWidget(self.effects_list)
        
        # Add status text box with larger height
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFont(button_font)
        self.status_text.setStyleSheet(STATUS_TEXT_STYLE)
        self.status_text.setMinimumHeight(100)  # Changed from 200 to 100
        left_layout.addWidget(self.status_text)
        
        # Create bottom buttons with styling
        bottom_buttons_layout = QHBoxLayout()
        
        # Create clear button
        self.clear_status_button = QPushButton("🗑️")  # Unicode trash can emoji
        self.clear_status_button.setToolTip("Clear status messages")
        self.clear_status_button.setFixedWidth(30)
        self.clear_status_button.setStyleSheet(CLEAR_STATUS_BUTTON_STYLE)
        self.clear_status_button.clicked.connect(self.status_text.clear)
        
        # Create other buttons with exact sizing
        self.reset_button = QPushButton("Reset")
        reset_width = self.reset_button.fontMetrics().horizontalAdvance("Reset") + 40
        self.reset_button.setFixedWidth(reset_width)
        
        self.save_button = QPushButton("Save Image")
        save_width = self.save_button.fontMetrics().horizontalAdvance("Save Image") + 40
        self.save_button.setFixedWidth(save_width)
        
        self.convert_directory_button = QPushButton("Convert Directory")
        convert_width = self.convert_directory_button.fontMetrics().horizontalAdvance("Convert Directory") + 40
        self.convert_directory_button.setFixedWidth(convert_width)
        
        # Add buttons to bottom layout
        bottom_buttons_layout.addWidget(self.clear_status_button)
        bottom_buttons_layout.addWidget(self.reset_button)
        bottom_buttons_layout.addWidget(self.save_button)
        bottom_buttons_layout.addWidget(self.convert_directory_button)
        left_layout.addLayout(bottom_buttons_layout)
        
        # Add transparency checkbox
        self.transparency_checkbox = QCheckBox("Save Image(s) with Transparent Background")
        self.transparency_checkbox.setChecked(True)  # Set default to checked
        self.transparency_checkbox.setFont(button_font)
        self.transparency_checkbox.setStyleSheet(TRANSPARENCY_CHECKBOX_STYLE)
        left_layout.addWidget(self.transparency_checkbox)
        
        # Create exit button with adjusted size
        self.exit_button = QPushButton("Exit")
        self.exit_button.setStyleSheet(EXIT_BUTTON_STYLE)
        left_layout.addWidget(self.exit_button)
        
        # Set fonts and connect signals
        for button in [self.reset_button, self.save_button, 
                      self.convert_directory_button, self.exit_button]:
            button.setFont(button_font)
        self.transparency_checkbox.setFont(button_font)
        
        self.reset_button.clicked.connect(self.reset_adjustments)
        self.save_button.clicked.connect(self.save_image)
        self.convert_directory_button.clicked.connect(self.convert_directory)
        self.exit_button.clicked.connect(self.close)
        
        # Create navigation and image display with fixed proportions
        self.image_container = QWidget()
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(IMAGE_LABEL_STYLE)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.prev_button = QPushButton("←")
        self.next_button = QPushButton("→")
        nav_font = QFont()
        nav_font.setPointSize(48)
        self.prev_button.setFont(nav_font)
        self.next_button.setFont(nav_font)
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        
        # Add image viewer to right side with fixed layout
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.image_label, 1)  # Use a stretch factor of 1
        nav_layout.addWidget(self.next_button)
        
        image_layout.addLayout(nav_layout)
        layout.addWidget(self.image_container, 1)  # Use a stretch factor of 1
        
        # Initialize remaining properties
        self.original_image = None
        self.adjusted_image = None
        self.color_offsets = {
            "cyan_red": 0,
            "magenta_green": 0,
            "yellow_blue": 0,
            "hue": 0
        }
        self.negative_applied = False
        self.background_color = None
        self.active_effects = {
            "Color Adjustments": [],
            "Special Effects": [],
            "Glow/Border Effects": []
        }
        
        # Left panel layout
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Gradient group layout
        gradient_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        gradient_layout.setSpacing(5)
        
        # Make gradient controls visible by default
        self.gradient_container.setVisible(True)
        
        # Add new state variables for tracking letter effects
        self.letter_image = None  # Stores the letter with its current effects
        self.current_letter_effects = {
            "slider_values": {},  # Store actual slider values
            "special_effect": "None"
        }
        
        # Initialize slider values
        for key in ["cyan_red", "magenta_green", "yellow_blue", "hue"]:
            self.current_letter_effects["slider_values"][key] = 0

    def showEvent(self, event):
        """Override show event to properly maximize after window is created"""
        super().showEvent(event)
        if self._should_maximize:
            self._should_maximize = False
            # Process events before attempting to maximize
            QApplication.processEvents()
            # Get available geometry to respect screen boundaries
            available_geometry = self.screen().availableGeometry()
            self.setGeometry(available_geometry)

    def create_slider(self, label_text, offset_key, min_val=-100, max_val=100):
        """Creates a slider without adding it to any layout"""
        slider_label = QLabel(label_text)
        label_font = QFont()
        label_font.setPointSize(label_font.pointSize() + 1)
        slider_label.setFont(label_font)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(0)
        slider.sliderReleased.connect(self.apply_adjustments)
        self.sliders[offset_key] = slider
        
        # Return both widgets so they can be added to appropriate layout later
        return slider_label, slider

    def load_directory(self):
        onedrive_path = os.path.expanduser("~/OneDrive")
        default_path = os.path.join(onedrive_path, "VectorProgram", "Scripts", "Alphabet Scripts", "Alphabets")
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", default_path)
        if directory:
            self.current_directory = directory
            self.directory_label.setText(directory.split('/')[-1])
            self.image_files = [f for f in os.listdir(directory)
                                if f.lower().startswith('image') and f.lower().endswith('.png')]
            self.image_files.sort()
            self.current_image_index = 0
            self.status_text.append(f"Found {len(self.image_files)} image files in directory")
            self.status_text.repaint()
            self.load_current_image()

    def load_current_image(self):
        """Load and display the current image without triggering layout changes"""
        if not self.image_files:
            return
            
        image_path = os.path.join(self.current_directory, self.image_files[self.current_image_index])
        self.original_image = Image.open(image_path).convert("RGBA")
        
        # Store original size for reference
        self.original_size = self.original_image.size
        
        # Only adjust size if needed for effects
        if self.current_glow != "None":
            self.adjust_image_size()
        
        self.adjusted_image = self.original_image.copy()
        self.update_image()

    def adjust_image_size(self):
        """Adjust image size based on border/glow width"""
        if not self.original_image or self.current_glow == "None":
            return
            
        border_width = self.border_width_slider.value()
        
        self.status_text.append(f"Adjusting image size for {self.current_glow} effect...")
        self.status_text.repaint()
        
        # Use the function from ImageEffects.py
        self.original_image = adjust_image_size(self.original_image, self.current_glow, border_width)
        self.adjusted_image = self.original_image.copy()
        
        self.status_text.append("Image size adjusted.")
        self.status_text.repaint()

    def update_image(self):
        """Update the displayed image without changing layout dimensions"""
        if self.adjusted_image:
            # Calculate the available space in the image label
            label_width = self.image_label.width()
            label_height = self.image_label.height()
            
            if label_width <= 0 or label_height <= 0:
                return  # Avoid scaling with invalid dimensions
                
            # Convert the image to QPixmap
            qt_image = ImageQt.ImageQt(self.adjusted_image)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale the image to fit in the available space while preserving aspect ratio
            scaled_pixmap = pixmap.scaled(
                label_width,
                label_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            
            # Set the pixmap without changing the label's size
            self.image_label.setPixmap(scaled_pixmap)

    def apply_adjustments(self):
        if not self.original_image:
            return
        
        # Check if letter effects have changed by comparing actual values
        letter_effects_changed = False
        
        # Check if any slider values have changed
        for key in self.sliders:
            current_value = self.sliders[key].value()
            if current_value != self.current_letter_effects["slider_values"][key]:
                letter_effects_changed = True
                break
        
        # Also check if special effect changed
        if not letter_effects_changed:
            letter_effects_changed = (self.current_effect != self.current_letter_effects["special_effect"])
        
        # Build status message showing all active effects
        effects = []
        if any(self.sliders[key].value() != 0 for key in self.sliders):
            effects.append("Color Adjustments")
        if self.current_effect != "None":
            effects.append(self.current_effect)
        if self.current_glow != "None":
            effects.append(self.current_glow)
            
        # Clear status text and show processing message
        self.status_text.clear()
        if effects:
            self.status_text.append("Starting Processing: " + ", ".join(effects))
        else:
            self.status_text.append("Resetting to original")
        self.status_text.repaint()
        
        # Process letter effects only if they've changed
        if letter_effects_changed or self.letter_image is None:
            # Start with original image for letter effects
            self.letter_image = self.original_image.copy()
            
            # Apply color adjustments and special effects to letter using NumPy
            if any(self.sliders[key].value() != 0 for key in self.sliders):
                # Convert image to NumPy array
                img_array = np.array(self.letter_image)
                
                # Get alpha channel
                alpha = img_array[:, :, 3]
                
                # Only process non-transparent pixels
                mask = alpha > 0
                
                if mask.any():  # Only process if there are non-transparent pixels
                    # Get RGB values and normalize
                    rgb = img_array[mask, :3].astype(np.float32) / 255.0
                    
                    # Calculate HSV
                    max_val = np.max(rgb, axis=1)
                    min_val = np.min(rgb, axis=1)
                    diff = max_val - min_val
                    
                    # Calculate Hue
                    h = np.zeros_like(max_val)
                    diff_mask = diff != 0
                    
                    # Red is maximum
                    idx = (rgb[:, 0] == max_val) & diff_mask
                    h[idx] = (rgb[idx, 1] - rgb[idx, 2]) / diff[idx] % 6
                    
                    # Green is maximum
                    idx = (rgb[:, 1] == max_val) & diff_mask
                    h[idx] = (rgb[idx, 2] - rgb[idx, 0]) / diff[idx] + 2
                    
                    # Blue is maximum
                    idx = (rgb[:, 2] == max_val) & diff_mask
                    h[idx] = (rgb[idx, 0] - rgb[idx, 1]) / diff[idx] + 4
                    
                    h = (h / 6.0 + self.sliders["hue"].value() / 360.0) % 1.0
                    
                    # Calculate Saturation and Value
                    s = np.divide(diff, max_val, out=np.zeros_like(diff), where=max_val!=0)
                    v = max_val
                    
                    # Convert back to RGB
                    c = v * s
                    h_prime = h * 6.0
                    x = c * (1 - np.abs(h_prime % 2 - 1))
                    m = v - c
                    
                    # Initialize output RGB array
                    rgb_out = np.zeros_like(rgb)
                    
                    # Apply RGB conversion based on hue
                    idx = (h_prime < 1)
                    rgb_out[idx] = np.column_stack((c[idx], x[idx], np.zeros_like(x[idx])))
                    
                    idx = (h_prime >= 1) & (h_prime < 2)
                    rgb_out[idx] = np.column_stack((x[idx], c[idx], np.zeros_like(x[idx])))
                    
                    idx = (h_prime >= 2) & (h_prime < 3)
                    rgb_out[idx] = np.column_stack((np.zeros_like(x[idx]), c[idx], x[idx]))
                    
                    idx = (h_prime >= 3) & (h_prime < 4)
                    rgb_out[idx] = np.column_stack((np.zeros_like(x[idx]), x[idx], c[idx]))
                    
                    idx = (h_prime >= 4) & (h_prime < 5)
                    rgb_out[idx] = np.column_stack((x[idx], np.zeros_like(x[idx]), c[idx]))
                    
                    idx = (h_prime >= 5)
                    rgb_out[idx] = np.column_stack((c[idx], np.zeros_like(x[idx]), x[idx]))
                    
                    # Add back the value offset
                    rgb_out = (rgb_out + m[:, np.newaxis]) * 255
                    
                    # Apply color balance adjustments
                    cr_offset = (self.sliders["cyan_red"].value() / 100) * 0.5
                    mg_offset = (self.sliders["magenta_green"].value() / 100) * 0.5
                    yb_offset = (self.sliders["yellow_blue"].value() / 100) * 0.5
                    
                    rgb_out[:, 0] += cr_offset * 255
                    rgb_out[:, 1] += mg_offset * 255
                    rgb_out[:, 2] += yb_offset * 255
                    
                    # Clip values to valid range
                    rgb_out = np.clip(rgb_out, 0, 255).astype(np.uint8)
                    
                    # Update the image array
                    img_array[mask, :3] = rgb_out
                    
                    # Convert back to PIL Image
                    self.letter_image = Image.fromarray(img_array)
            
            # Apply special effect to the color-adjusted letter
            if self.current_effect != "None":
                self.letter_image = apply_color_option(self.current_effect, self.letter_image)
            
            # Update current letter effects state with actual values
            for key in self.sliders:
                self.current_letter_effects["slider_values"][key] = self.sliders[key].value()
            self.current_letter_effects["special_effect"] = self.current_effect
        
        # Start with current letter state
        self.adjusted_image = self.letter_image.copy()
            
        # Apply glow/border as a separate effect with its own color
        if self.current_glow != "None":
            # Create larger canvas for glow
            glow_width = self.border_width_slider.value()
            padding = glow_width * 8 if self.current_glow == "glow" else glow_width * 4
            
            # Create new image with padding
            new_width = self.adjusted_image.width + padding
            new_height = self.adjusted_image.height + padding
            final_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            
            # Paste the letter image in center
            paste_x = padding // 2
            paste_y = padding // 2
            final_image.paste(self.adjusted_image, (paste_x, paste_y))
            
            # Apply glow/border effect with its own color
            self.adjusted_image = apply_glow_effect(self.current_glow, final_image, self.start_color_slider, self.border_width_slider)
        
        self.update_image()
        self.status_text.append("Completed Processing.")
        self.status_text.repaint()
        self.update_effects_list()

    def reset_adjustments(self):
        if self.original_image:
            self.letter_image = None
            self.adjusted_image = self.original_image.copy()
            
            # Reset all sliders to 0
            for slider in self.sliders.values():
                slider.setValue(0)
            
            # Reset effect buttons
            for button in self.findChildren(QPushButton):
                if button.isCheckable():
                    button.setChecked(button.text() == "None")
            
            self.current_effect = "None"
            self.current_glow = "None"
            
            # Reset letter effects state with all slider values at 0
            self.current_letter_effects = {
                "slider_values": {
                    "cyan_red": 0,
                    "magenta_green": 0,
                    "yellow_blue": 0,
                    "hue": 0
                },
                "special_effect": "None"
            }
            
            self.update_image()
            self.update_effects_list()

    def save_image(self):
        if not self.adjusted_image:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PNG Image",
            self.current_directory if self.current_directory else "",
            "PNG (*.png)"
        )
        if file_path:
            if not file_path.lower().endswith('.png'):
                file_path += '.png'
            save_image_with_transparency(self.adjusted_image, file_path, self.transparency_checkbox.isChecked())
            self.status_text.append(f"Image saved: {os.path.basename(file_path)}")

    def convert_directory(self):
        if not self.current_directory:
            self.status_text.append("Error: Please load a directory first")
            return
        dialog = QInputDialog(self)
        dialog.setWindowTitle("New Directory Name")
        adjustments = []
        if self.negative_applied:
            adjustments.append("Negative effect")
        if self.sliders["cyan_red"].value() != 0:
            adjustments.append(f"Cyan-Red: {self.sliders['cyan_red'].value()}%")
        if self.sliders["magenta_green"].value() != 0:
            adjustments.append(f"Magenta-Green: {self.sliders['magenta_green'].value()}%")
        if self.sliders["yellow_blue"].value() != 0:
            adjustments.append(f"Yellow-Blue: {self.sliders['yellow_blue'].value()}%")
        if self.sliders["hue"].value() != 0:
            adjustments.append(f"Hue rotation: {self.sliders['hue'].value()}°")
        selected_option = self.current_effect
        if selected_option != "None":
            adjustments.append(f"Color Option: {selected_option}")
        adjustments_text = "Current adjustments to be applied:\n" + "\n".join(adjustments) if adjustments else "No adjustments to be applied"
        dialog.setLabelText(f"{adjustments_text}\n\nEnter name for output directory:")
        dialog.resize(dialog.width() * 2, dialog.height() * 2)
        dialog.setFont(self.font())
        if not dialog.exec() or not dialog.textValue():
            return
        directory_name = dialog.textValue()
        onedrive_path = os.path.expanduser("~/OneDrive")
        output_path = os.path.join(onedrive_path, "VectorProgram", "Scripts", "Alphabet Scripts", "Alphabets", directory_name)
        try:
            os.makedirs(output_path, exist_ok=True)
            self.status_text.append(f"Created output directory: {directory_name}")
            self.status_text.repaint()
            cr_offset = (self.sliders["cyan_red"].value() / 100) * 0.5
            mg_offset = (self.sliders["magenta_green"].value() / 100) * 0.5
            yb_offset = (self.sliders["yellow_blue"].value() / 100) * 0.5
            hue_offset = self.sliders["hue"].value() / 360.0
            for image_file in self.image_files:
                input_path = os.path.join(self.current_directory, image_file)
                output_file = os.path.join(output_path, image_file)
                img = Image.open(input_path).convert("RGBA")
                pixels = img.load()
                width, height = img.size
                for j in range(height):
                    for i in range(width):
                        r, g, b, a = pixels[i, j]
                        pixels[i, j] = self.adjust_pixel(r, g, b, a, cr_offset, mg_offset, yb_offset, hue_offset)
                self.adjusted_image = img.copy()
                self.background_color = self.background_color
                if selected_option != "None":
                    self.apply_color_option(selected_option)
                    img = self.adjusted_image
                if self.negative_applied:
                    for j in range(height):
                        for i in range(width):
                            r, g, b, a = pixels[i, j]
                            if a == 0:
                                continue
                            pixels[i, j] = (255 - r, 255 - g, 255 - b, a)
                    self.background_color = (255 - self.background_color[0], 255 - self.background_color[1], 255 - self.background_color[2])
                self.save_image_with_transparency(img, output_file, self.transparency_checkbox.isChecked())
                self.status_text.append(f"Processed: {image_file}")
                self.status_text.repaint()
                QApplication.processEvents()
            self.status_text.append("Directory conversion complete!")
            self.status_text.repaint()
        except Exception as e:
            self.status_text.append(f"Error: {str(e)}")
            self.status_text.repaint()

    def toggle_background(self):
        if not self.image_label:
            return
        self.display_background_as_black = not self.display_background_as_black
        self.update_image()

    def prev_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.load_current_image()

    def next_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.load_current_image()

    def update_effects_list(self):
        effects = {
            "Color Adjustments": [],
            "Special Effects": [],
            "Glow/Border Effects": []
        }
        
        # Check color adjustments
        for slider_name, slider in self.sliders.items():
            if slider.value() != 0:
                effects["Color Adjustments"].append(
                    f"{slider_name.replace('_', '-').title()}: {slider.value()}"
                )
        
        # Check special effects
        if self.current_effect != "None":
            effects["Special Effects"].append(self.current_effect)
        
        # Check glow/border effects – record effect type, width, and resize padding details
        if self.current_glow in ["glow", "border"]:  # Check for specific effect types
            width_val = self.border_width_slider.value()
            if self.current_glow == "glow":
                padding_val = width_val * 8
                effect_name = "Glow"
            else:  # border
                padding_val = width_val * 4
                effect_name = "Border"
            effects["Glow/Border Effects"].append(
                f"{effect_name} Effect (Width: {width_val}, Resize padding: {padding_val}px)"
            )
        
        self.active_effects = effects
        self.effects_list.update_effects(effects)

    def _select_button(self, effect_name, valid_effects, current_effect_attr):
        """Generic button selection handler"""
        for button in self.findChildren(QPushButton):
            if button.isCheckable() and button.text() in valid_effects:
                button.setChecked(button.text() == effect_name)
        
        setattr(self, current_effect_attr, effect_name)

    def select_effect(self, effect_name):
        """Handle effect button selection"""
        self._select_button(effect_name, self.available_effects, 'current_effect')
        self.apply_adjustments()

    def select_glow(self, effect_name):
        """Handle glow/border button selection"""
        self._select_button(effect_name, self.available_glow_effects, 'current_glow')
        self.apply_adjustments()

    def update_width_label(self):
        """Update the width value label when slider changes"""
        self.width_value_label.setText(str(self.border_width_slider.value()))

    def update_color_preview(self, which):
        """Update color preview for either start or end color"""
        if which == "start":
            hue = self.start_color_slider.value() / 360.0
            preview = self.start_color_preview
        else:
            hue = self.end_color_slider.value() / 360.0
            preview = self.end_color_preview
            
        r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
        preview.setStyleSheet(get_color_preview_style(r, g, b))
        self.update_gradient()

    def update_gradient(self):
        """Update gradient preview and effect if active"""
        if self.glow_button.isChecked() or self.border_button.isChecked():
            self.apply_adjustments()

    def get_gradient_colors(self, x, y, width, height):
        """Calculate color based on position and current settings"""
        start_hue = self.start_color_slider.value() / 360.0
        
        if not self.single_color_mode.isChecked():  # Double color mode
            end_hue = self.end_color_slider.value() / 360.0
        else:  # Single color mode - shift hue slightly for gradient
            end_hue = (start_hue + 0.15) % 1.0  # Subtle shift for single color gradient
        
        gradient_type = self.gradient_type.currentText()
        gradient_direction = self.gradient_direction.currentText()
        
        # Use the function from ImageEffects.py
        return get_gradient_colors(x, y, width, height, start_hue, end_hue, gradient_type, gradient_direction)

    def toggle_color_mode(self, state):
        """Toggle between single color and gradient mode"""
        is_double = bool(state)  # Now true means double color mode
        self.end_color_container.setVisible(is_double)
        self.gradient_container.setVisible(is_double)
        self.start_color_label.setText("Start Color:" if is_double else "Color:")
        
        # Update buttons text
        self.glow_button.setText("Apply Gradient Glow" if is_double else "Apply Color Glow")
        self.border_button.setText("Apply Gradient Border" if is_double else "Apply Color Border")
        
        # Update effect if active
        if self.glow_button.isChecked() or self.border_button.isChecked():
            self.apply_adjustments()

    def adjust_size_for_glow(self):
        """Adjust image size for glow using the current adjusted image"""
        if not self.adjusted_image:
            return
        
        border_width = self.border_width_slider.value()
        self.status_text.append(f"Adjusting image size for {self.current_glow} effect...")
        self.status_text.repaint()
        
        # Use the function from ImageEffects.py
        self.adjusted_image = adjust_size_for_glow(self.adjusted_image, self.current_glow, border_width)
        
        self.status_text.append("Image size adjusted.")
        self.status_text.repaint()

    def handle_glow_click(self, effect_type):
        """Handle glow/border button click"""
        # Update current glow type
        self.current_glow = effect_type
        
        # Update button states
        self.none_glow_button.setChecked(effect_type == "None")
        self.glow_button.setChecked(effect_type == "glow")
        self.border_button.setChecked(effect_type == "border")
        
        # Apply all effects with new glow setting
        self.apply_adjustments()

    def open_directory_explorer(self):
        """Opens the current directory in Explorer on the second monitor"""
        if not self.current_directory:
            self.status_text.append("No directory loaded")
            return
            
        try:
            # Normalize path for Windows
            dir_path = os.path.normpath(self.current_directory)
            
            # First try to find and focus existing window
            ps_find_window = f'''
            $shell = New-Object -ComObject Shell.Application
            $found = $false
            $windows = $shell.Windows()
            foreach ($window in $windows) {{
                try {{
                    $path = $window.Document.Folder.Self.Path
                    if ($path -eq '{dir_path}') {{
                        # Found existing window
                        $found = $true
                        $window.Visible = $true
                        
                        # Activate the window and bring to front
                        $signature = @"
                        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
                        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                        "@
                        Add-Type -MemberDefinition $signature -Name Win32Utils -Namespace Win32
                        $hwnd = $window.HWND
                        [Win32.Win32Utils]::ShowWindow($hwnd, 9)  # SW_RESTORE = 9
                        [Win32.Win32Utils]::SetForegroundWindow($hwnd)
                        
                        # Try to move to second monitor if available
                        Add-Type -AssemblyName System.Windows.Forms
                        $screens = [System.Windows.Forms.Screen]::AllScreens
                        if ($screens.Count -gt 1) {{
                            $second = $screens[1]
                            $window.Left = $second.Bounds.X
                            $window.Top = $second.Bounds.Y
                            $window.Width = $second.Bounds.Width
                            $window.Height = $second.Bounds.Height
                        }}
                        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($window) | Out-Null
                        break
                    }}
                }} catch {{}}
            }}
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($windows) | Out-Null
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
            $found
            '''
            
            # Execute PowerShell to find existing window
            import subprocess
            result = subprocess.run(['powershell', '-Command', ps_find_window], capture_output=True, text=True)
            
            # If window wasn't found, open new one
            if 'False' in result.stdout:
                # Open new Explorer window
                subprocess.run(['explorer.exe', dir_path])
                
                # Wait and move to second monitor
                ps_move_window = f'''
                Start-Sleep -Milliseconds 500
                Add-Type -AssemblyName System.Windows.Forms
                $screens = [System.Windows.Forms.Screen]::AllScreens
                if ($screens.Count -gt 1) {{
                    $second = $screens[1]
                    $shell = New-Object -ComObject Shell.Application
                    $windows = $shell.Windows()
                    foreach ($window in $windows) {{
                        try {{
                            $path = $window.Document.Folder.Self.Path
                            if ($path -eq '{dir_path}') {{
                                $window.Left = $second.Bounds.X
                                $window.Top = $second.Bounds.Y
                                $window.Width = $second.Bounds.Width
                                $window.Height = $second.Bounds.Height
                                break
                            }}
                        }} catch {{}}
                    }}
                }}
                '''
                subprocess.run(['powershell', '-Command', ps_move_window], capture_output=True)
            
            self.status_text.append("Opened directory in Explorer")
        except Exception as e:
            self.status_text.append(f"Error opening directory: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorBalanceApp()
    window.show()
    sys.exit(app.exec())