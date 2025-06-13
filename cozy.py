import sys
import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QFrame, QLabel, QMenuBar, QAction,
    QMessageBox, QWidget, QCheckBox, QStackedWidget, QSplitter, QSlider
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPalette, QColor, QFont
import unidecode


# 🔹 Functie pentru cautare DuckDuckGo ( deoarece va indexa mai multe rezultate, chiar si cele ascunse de Google sau Bing sau etc))
def perform_duckduckgo_search(query, num_results=5):
    search_url = f"https://duckduckgo.com/html/?q={query}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            raise Exception(f"DuckDuckGo Search failed: HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        search_results = []

        for result in soup.select(".result__a"):
            title = result.text.strip()
            raw_link = result["href"].strip()

            if "uddg=" in raw_link:
                encoded_url = raw_link.split("uddg=")[-1]
                decoded_url = urllib.parse.unquote(encoded_url)
                search_results.append((title, decoded_url))
            else:
                search_results.append((title, raw_link))

        return search_results

    except Exception as e:
        print(f"Eroare la căutare DuckDuckGo: {e}")
        return []


# 🔹 Functie pentru extragerea versurilor
def extract_lyrics_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            return "Eroare la încărcarea paginii!"

        soup = BeautifulSoup(response.text, "html.parser")
        lyrics = []

        #  Selectam doar zona corecta a versurilor (pentru site-ul resursecrestine.ro; iar pt restul, default)
        lyrics_div = soup.select_one("body > div.trc-body div.container-fluid.trc-wrapper div:nth-child(2) div.col-lg-7.order-lg-2.mb-3 div:nth-child(5) div")

        if lyrics_div:
            lyrics = lyrics_div.get_text("\n", strip=True).split("\n")

        return "\n\n".join(lyrics)[:1500]

    except Exception as e:
        print(f"Eroare la extragerea versurilor: {e}")
        return "Nu s-au putut extrage versurile!"


# 🔹 Functie pentru eliminarea cifrelor si punctelor
def remove_numbers_and_dots(text):
    return re.sub(r'\d+\.?', '', text)


# 🔹 Clasa pentru pagina de cautare Bible.com
class BibleSearchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: rgba(45, 45, 45, 0.9); color: white; border-radius: 10px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 🔹 Splitter pentru a împărți fereastra în două jumătăți egale
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # 🔹 Jumătatea stângă - Box-ul de căutare
        self.left_frame = QWidget()
        self.left_layout = QVBoxLayout(self.left_frame)
        self.splitter.addWidget(self.left_frame)

        # 🔹 Jumătatea dreaptă - Box-ul de rezultate
        self.right_frame = QWidget()
        self.right_layout = QVBoxLayout(self.right_frame)
        self.splitter.addWidget(self.right_frame)

        # 🔹 Încărcăm box-ul de căutare
        self.load_search_box()

        # 🔹 Setăm dimensiuni egale pentru cele două jumătăți
        self.splitter.setSizes([self.width() // 2, self.width() // 2])

    def load_search_box(self):
        # 🔹 Încărcăm conținutul box-ului de căutare de pe site
        search_box_url = "https://www.ebible.ro/cautare-avansata.php"
        self.search_view = QWebEngineView()
        self.search_view.setUrl(QUrl(search_box_url))
        self.left_layout.addWidget(self.search_view)

        # 🔹 Extragem box-ul de rezultate (inițial gol)
        self.result_view = QWebEngineView()
        self.result_view.setStyleSheet("background-color: rgba(45, 45, 45, 0.9); border-radius: 10px;")
        self.right_layout.addWidget(self.result_view)

        # 🔹 Ascultăm pentru schimbări de URL (pentru a detecta căutarea)
        self.search_view.urlChanged.connect(self.handle_url_change)

    def handle_url_change(self, url):
        # 🔹 Dacă URL-ul conține "cautare-expresie.php", înseamnă că s-a făcut o căutare
        if "cautare-expresie.php" in url.toString():
            self.update_results(url.toString())
            # 🔹 Redirecționăm box-ul din stânga înapoi la pagina de căutare avansată
            self.search_view.setUrl(QUrl("https://www.ebible.ro/cautare-avansata.php"))

    def update_results(self, results_url):
        # 🔹 Încărcăm conținutul box-ului de rezultate de pe site
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        }
        response = requests.get(results_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # 🔹 Extragem doar box-ul de rezultate
        result_box = soup.select_one("#content")  # Selectorul pentru box-ul de rezultate
        if result_box:
            result_box_html = str(result_box)
            self.result_view.setHtml(self.apply_glassmorphism_to_html(result_box_html))

    def apply_glassmorphism_to_html(self, html_content):
        # 🔹 CSS pentru efectul de glassmorphism (fără inversare culori)
        glassmorphism_css = """
        <style>
            body {
                background-color: rgba(45, 45, 45, 0.9);
                color: #e0e0e0;
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                border-radius: 10px;
                padding: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            input, select, button {
                background-color: rgba(68, 68, 68, 0.9);
                color: #e0e0e0;
                border: 1px solid rgba(85, 85, 85, 0.3);
                padding: 5px;
                border-radius: 5px;
            }
            a {
                color: #4dabf7;
            }
            .alert-light {
                background-color: rgba(68, 68, 68, 0.9) !important;
                color: #e0e0e0 !important;
            }
            .text-dark {
                color: #e0e0e0 !important;
            }
            .text-danger {
                color: #ff6b6b !important;
            }
        </style>
        """
        # Adăugăm CSS-ul la conținutul HTML
        return f"<html><head>{glassmorphism_css}</head><body>{html_content}</body></html>"


# 🔹 Aplicația principală
class SimpleSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Căutare Simplă - Cântări și Versete")
        self.setGeometry(100, 100, 800, 500)

        # Setare temă ultra modernă
        self.set_ultra_modern_theme()

        # 🔹 Stacked Widget pentru a gestiona paginile
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 🔹 Pagina F1 - Căutare cântări
        self.song_search_page = self.create_song_search_page()
        self.stacked_widget.addWidget(self.song_search_page)

        # 🔹 Pagina F2 - Căutare versete
        self.bible_search_page = BibleSearchPage()
        self.stacked_widget.addWidget(self.bible_search_page)

        # 🔹 Shortcut-uri pentru navigare
        self.setup_shortcuts()

    def set_glassmorphism_theme(self):
        # Setăm tema de glassmorphism pentru întreaga aplicație
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgba(30, 30, 30, 0.9);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QWidget {
                background-color: transparent;
                color: white;
            }
            QLineEdit, QListWidget, QFrame {
                background-color: rgba(68, 68, 68, 0.9);
                color: white;
                border-radius: 5px;
                border: 1px solid rgba(85, 85, 85, 0.3);
            }
            QSlider::groove:horizontal {
                background-color: rgba(68, 68, 68, 0.9);
                border-radius: 2px;
                height: 5px;
            }
            QSlider::handle:horizontal {
                background-color: #4dabf7;
                width: 15px;
                height: 15px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QCheckBox {
                color: white;
            }
            QLabel {
                color: white;
            }
            QMenuBar {
                background-color: rgba(45, 45, 45, 0.9);
                color: white;
                border-radius: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: rgba(68, 68, 68, 0.9);
            }
        """)

    def set_ultra_modern_theme(self):
        """Apply an ultra-modern dark theme using gradients and sleek colors."""
        modern_style = """
            QWidget {
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                color: #f1f1f1;
                background-color: transparent;
            }
            QMainWindow {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #141414, stop:1 #232323);
                border-radius: 12px;
                border: 1px solid #2d2d2d;
            }
            QLineEdit, QListWidget, QFrame {
                background-color: rgba(40, 40, 40, 0.85);
                border: 1px solid #303030;
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #005fb8;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background-color: #2d2d2d;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #0078d7;
                border: none;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QMenuBar {
                background-color: transparent;
            }
            QMenuBar::item {
                padding: 6px 15px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #2d2d2d;
            }
        """
        self.setStyleSheet(modern_style)

    def create_song_search_page(self):
        # 🔹 Pagina pentru căutare cântări
        page = QWidget()
        layout = QHBoxLayout(page)

        # 🔹 Secțiunea stângă (căutare + rezultate)
        left_frame = QWidget()
        left_layout = QVBoxLayout(left_frame)
        layout.addWidget(left_frame)

        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Introduceți cântarea...")
        search_bar.setStyleSheet("background-color: rgba(68, 68, 68, 0.9); color: white; border-radius: 5px; padding: 5px;")
        search_bar.returnPressed.connect(self.perform_search)
        left_layout.addWidget(search_bar)

        results_list = QListWidget()
        results_list.setStyleSheet("background-color: rgba(68, 68, 68, 0.9); color: white; border-radius: 5px;")
        results_list.itemClicked.connect(self.copy_to_clipboard)
        results_list.setMouseTracking(True)
        results_list.itemEntered.connect(self.show_hover_window)
        left_layout.addWidget(results_list)

        # 🔹 Checkbox pentru eliminare diacritice și mesaj de confirmare
        checkbox_layout = QHBoxLayout()
        self.remove_diacritics_checkbox = QCheckBox("Elimină diacritice")
        self.remove_diacritics_checkbox.setStyleSheet("color: white;")
        self.copy_status_label = QLabel()
        self.copy_status_label.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.remove_diacritics_checkbox)
        checkbox_layout.addWidget(self.copy_status_label)
        left_layout.addLayout(checkbox_layout)

        # 🔹 Bară de transparență
        transparency_slider = QSlider(Qt.Horizontal)
        transparency_slider.setMinimum(30)
        transparency_slider.setMaximum(100)
        transparency_slider.setValue(100)
        transparency_slider.valueChanged.connect(self.set_transparency)
        left_layout.addWidget(QLabel("Transparență:"))
        left_layout.addWidget(transparency_slider)

        # 🔹 Secțiunea dreaptă (spațiu blank pentru hover)
        right_frame = QFrame()
        right_frame.setFixedWidth(360)
        right_frame.setStyleSheet("background-color: rgba(51, 51, 51, 0.9); border-radius: 10px;")
        layout.addWidget(right_frame)

        # Inițializare hover window (cu dark mode forțat)
        self.hover_window = QWebEngineView()
        self.hover_window.setStyleSheet("background-color: black;")  # Fundal negru
        self.hover_window.setHtml("""
        <style>
            body {
                background-color: black;  /* Fundal negru */
                filter: invert(1) hue-rotate(180deg);  /* Inversează culorile */
            }
            img, video, iframe {
                filter: invert(1) hue-rotate(180deg);  /* Inversează culorile pentru imagini și video */
            }
        </style>
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(self.hover_window)

        # Salvăm referințe pentru a le folosi mai târziu
        self.search_bar = search_bar
        self.results_list = results_list

        return page

    def perform_search(self):
        query = self.search_bar.text().strip()
        self.results_list.clear()
        if not query:
            self.results_list.addItem("Introduceți un termen de căutare!")
            return

        results = perform_duckduckgo_search(query, num_results=5)
        if results:
            for title, link in results:
                self.results_list.addItem(f"{title} - {link}")
        else:
            self.results_list.addItem("Niciun rezultat găsit.")

    def copy_to_clipboard(self, item):
        if not item:
            return

        link = item.text().split(" - ")[-1]
        content = extract_lyrics_from_url(link)

        if self.remove_diacritics_checkbox.isChecked():
            content = unidecode.unidecode(content)

        # Eliminăm cifrele și punctele
        content = remove_numbers_and_dots(content)

        clipboard = QApplication.clipboard()
        clipboard.setText(content)

        # Afișăm mesajul de confirmare
        if content and len(content) > 0:
            self.copy_status_label.setText("Copiat")
            self.copy_status_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self.copy_status_label.setText("Eroare")
            self.copy_status_label.setStyleSheet("color: red; font-size: 12px;")

    def show_hover_window(self, item):
        if not item:
            return

        link = item.text().split(" - ")[-1]
        self.hover_window.setUrl(QUrl(link))

    def set_transparency(self, value):
        # Setăm transparența pentru întreaga aplicație
        self.setWindowOpacity(value / 100)

    def setup_shortcuts(self):
        # 🔹 Shortcut pentru pagina F1 - Căutare cântări
        shortcut_f1 = QAction(self)
        shortcut_f1.setShortcut("F1")
        shortcut_f1.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.addAction(shortcut_f1)

        # 🔹 Shortcut pentru pagina F2 - Căutare versete.
        shortcut_f2 = QAction(self)
        shortcut_f2.setShortcut("F2")
        shortcut_f2.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.addAction(shortcut_f2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleSearchApp()
    window.show()
    sys.exit(app.exec_())
