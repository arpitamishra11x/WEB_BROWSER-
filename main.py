import sys
import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit,
    QTabWidget, QStatusBar, QFileDialog,
    QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# ----------------- App Constants -----------------
APP_NAME = "PyBrowser"
APP_VERSION = "1.2.0"
BOOKMARKS_FILE = "bookmarks.json"
HOME_PAGE = "https://www.google.com"


class BrowserTab(QWebEngineView):
    """Single browser tab."""
    def __init__(self, parent=None):
        super().__init__(parent)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        self.resize(1100, 800)

        # ----------------- Tabs -----------------
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # ----------------- Toolbar -----------------
        navtb = QToolBar("Navigation")
        navtb.setIconSize(QtCore.QSize(18, 18))
        self.addToolBar(navtb)
        self._add_nav_actions(navtb)

        # ----------------- URL Bar -----------------
        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Search or enter URL...")
        self.urlbar.returnPressed.connect(self.navigate_to_url_from_bar)
        navtb.addWidget(self.urlbar)

        go_btn = QAction("Go", self)
        go_btn.triggered.connect(self.navigate_to_url_from_bar)
        navtb.addAction(go_btn)

        # ----------------- Menu -----------------
        self.bookmarks_menu = self.menuBar().addMenu("Bookmarks")
        self.bookmarks_menu.addAction("Manage bookmarks...", self.manage_bookmarks)
        self.bookmarks_menu.addSeparator()

        tools_menu = self.menuBar().addMenu("Tools")
        tools_menu.addAction("Open File...", self.open_file)
        tools_menu.addAction("Save Page As...", self.save_page)
        tools_menu.addSeparator()
        tools_menu.addAction("Quit", self.close)

        # ----------------- Status Bar -----------------
        self.status = QStatusBar()
        self.status.showMessage("Ready | PyBrowser")
        self.setStatusBar(self.status)

        # ----------------- Shortcuts -----------------
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, activated=self.close_current_tab)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self, activated=self.focus_urlbar)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, activated=self.close)

        # ----------------- Bookmarks -----------------
        self.bookmarks = []
        self.load_bookmarks()
        self.refresh_bookmarks_menu()

        # ----------------- First Tab -----------------
        self.add_new_tab(HOME_PAGE, switch=True)

    # ======================================================
    # Toolbar helpers
    # ======================================================
    def _add_nav_actions(self, toolbar):
        actions = [
            ("Back", QtWidgets.QStyle.SP_ArrowBack, lambda: self.current_browser().back()),
            ("Forward", QtWidgets.QStyle.SP_ArrowForward, lambda: self.current_browser().forward()),
            ("Reload", QtWidgets.QStyle.SP_BrowserReload, lambda: self.current_browser().reload()),
            ("Stop", QtWidgets.QStyle.SP_BrowserStop, lambda: self.current_browser().stop()),
            ("Home", QtWidgets.QStyle.SP_DirHomeIcon, self.navigate_home),
        ]

        for text, icon, callback in actions:
            act = QAction(self.style().standardIcon(icon), text, self)
            act.triggered.connect(callback)
            toolbar.addAction(act)

        toolbar.addSeparator()

        new_tab = QAction("New Tab", self)
        new_tab.setShortcut("Ctrl+T")
        new_tab.triggered.connect(lambda: self.add_new_tab(HOME_PAGE, switch=True))
        toolbar.addAction(new_tab)

        bookmark = QAction("Bookmark", self)
        bookmark.triggered.connect(self.add_bookmark_for_current_page)
        toolbar.addAction(bookmark)

    # ======================================================
    # Tab Management
    # ======================================================
    def add_new_tab(self, qurl, switch=False):
        if isinstance(qurl, str):
            qurl = QUrl(qurl)

        for i in range(self.tabs.count()):
            if self.tabs.widget(i).url() == qurl:
                self.tabs.setCurrentIndex(i)
                return

        browser = BrowserTab()
        browser.setUrl(qurl)

        index = self.tabs.addTab(browser, "Loading...")
        browser.urlChanged.connect(lambda q, b=browser: self.update_urlbar(q, b))
        browser.loadFinished.connect(lambda _, b=browser: self.update_tab_title(b))
        browser.loadProgress.connect(self.update_progress)

        if switch:
            self.tabs.setCurrentIndex(index)

    def close_current_tab(self, index=None):
        if self.tabs.count() == 1:
            reply = QMessageBox.question(self, "Quit", "Close the browser?")
            if reply == QMessageBox.Yes:
                self.close()
            return

        if index is None:
            index = self.tabs.currentIndex()
        self.tabs.removeTab(index)

    def current_browser(self):
        return self.tabs.currentWidget()

    def current_tab_changed(self, _):
        self.update_urlbar(self.current_browser().url(), self.current_browser())

    def update_tab_title(self, browser):
        index = self.tabs.indexOf(browser)
        title = browser.title() or browser.url().host()
        self.tabs.setTabText(index, title)

    # ======================================================
    # Navigation
    # ======================================================
    def navigate_home(self):
        self.current_browser().setUrl(QUrl(HOME_PAGE))

    def navigate_to_url_from_bar(self):
        text = self.urlbar.text().strip()
        if not text:
            return

        if " " in text or "." not in text:
            search_url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
            self.current_browser().setUrl(QUrl(search_url))
            return

        if not text.startswith(("http://", "https://")):
            text = "https://" + text

        self.current_browser().setUrl(QUrl(text))

    def update_urlbar(self, qurl, browser):
        if browser != self.current_browser():
            return
        self.urlbar.setText(qurl.toString())
        self.urlbar.setCursorPosition(0)

    def update_progress(self, progress):
        self.status.showMessage(f"Loading... {progress}%")
        if progress == 100:
            self.status.showMessage("Ready | PyBrowser")

    # ======================================================
    # Bookmarks
    # ======================================================
    def load_bookmarks(self):
        try:
            if os.path.exists(BOOKMARKS_FILE):
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    self.bookmarks = json.load(f)
            else:
                self.bookmarks = []
        except (json.JSONDecodeError, IOError):
            self.bookmarks = []
            QMessageBox.warning(self, "Bookmarks", "Bookmarks file was reset due to an error.")

    def save_bookmarks(self):
        with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.bookmarks, f, indent=2)

    def refresh_bookmarks_menu(self):
        for action in self.bookmarks_menu.actions()[2:]:
            self.bookmarks_menu.removeAction(action)

        for bm in self.bookmarks:
            act = QAction(bm["title"], self)
            act.triggered.connect(lambda _, u=bm["url"]: self.add_new_tab(u, True))
            self.bookmarks_menu.addAction(act)

    def add_bookmark_for_current_page(self):
        browser = self.current_browser()
        url = browser.url().toString()
        title = browser.title() or url

        if any(b["url"] == url for b in self.bookmarks):
            QMessageBox.information(self, "Bookmark", "Already bookmarked.")
            return

        self.bookmarks.append({"title": title, "url": url})
        self.save_bookmarks()
        self.refresh_bookmarks_menu()

    def manage_bookmarks(self):
        QMessageBox.information(self, "Bookmarks", "Bookmark manager coming soon.")

    # ======================================================
    # File Operations
    # ======================================================
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file")
        if path:
            self.add_new_tab(QUrl.fromLocalFile(path).toString(), True)

    def save_page(self):
        browser = self.current_browser()

        def callback(html):
            path, _ = QFileDialog.getSaveFileName(self, "Save Page", "", "HTML Files (*.html)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)

        browser.page().toHtml(callback)

    # ======================================================
    def focus_urlbar(self):
        self.urlbar.setFocus()
        self.urlbar.selectAll()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Quit", "Exit browser?")
        event.accept() if reply == QMessageBox.Yes else event.ignore()


def main():
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

