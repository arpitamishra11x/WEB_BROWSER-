import sys
import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget, QWidget,
    QVBoxLayout, QStatusBar, QFileDialog, QMessageBox, QMenu
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

BOOKMARKS_FILE = "bookmarks.json"
HOME_PAGE = "https://www.google.com"


class BrowserTab(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyBrowser")
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        self.resize(1100, 800)

        # Central widget -- tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # Navigation toolbar
        navtb = QToolBar("Navigation")
        navtb.setIconSize(QtCore.QSize(18, 18))
        self.addToolBar(navtb)

        # Back
        back_btn = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowBack), "Back", self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navtb.addAction(back_btn)

        # Forward
        next_btn = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowForward), "Forward", self)
        next_btn.triggered.connect(lambda: self.current_browser().forward())
        navtb.addAction(next_btn)

        # Reload
        reload_btn = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload), "Reload", self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navtb.addAction(reload_btn)

        # Stop
        stop_btn = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserStop), "Stop", self)
        stop_btn.triggered.connect(lambda: self.current_browser().stop())
        navtb.addAction(stop_btn)

        # Home
        home_btn = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_DirHomeIcon), "Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        # URL bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url_from_bar)
        navtb.addWidget(self.urlbar)

        go_btn = QAction("Go", self)
        go_btn.triggered.connect(self.navigate_to_url_from_bar)
        navtb.addAction(go_btn)

        navtb.addSeparator()

        # New tab
        new_tab_action = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder), "New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(lambda _: self.add_new_tab(HOME_PAGE, switch=True))
        navtb.addAction(new_tab_action)

        # Bookmark button
        bookmark_action = QAction(self.style().standardIcon(QtWidgets.QStyle.SP_DriveHDIcon), "Bookmark", self)
        bookmark_action.triggered.connect(self.add_bookmark_for_current_page)
        navtb.addAction(bookmark_action)

        # Bookmarks menu in menubar
        menubar = self.menuBar()
        bookmarks_menu = menubar.addMenu("Bookmarks")
        self.bookmarks_menu = bookmarks_menu
        bookmarks_menu.addAction("Manage bookmarks...", self.manage_bookmarks)
        bookmarks_menu.addSeparator()

        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction("Open File...", self.open_file)
        tools_menu.addAction("Save Page As...", self.save_page)
        tools_menu.addSeparator()
        tools_menu.addAction("Quit", self.close)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Shortcuts
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, activated=self.close_current_tab)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self, activated=self.focus_urlbar)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, activated=self.close)

        # Load bookmarks
        self.bookmarks = []
        self.load_bookmarks()
        self.refresh_bookmarks_menu()

        # Add initial tab
        self.add_new_tab(HOME_PAGE, switch=True)

    # ----------------- Tab Management -----------------
    def add_new_tab(self, qurl=None, switch=False):
        if qurl is None:
            qurl = HOME_PAGE
        if isinstance(qurl, str):
            qurl = QUrl(qurl)
        browser = BrowserTab()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, "New Tab")
        # Connect signals
        browser.urlChanged.connect(lambda q, b=browser: self.update_urlbar(q, b))
        browser.loadFinished.connect(lambda ok, b=browser: self.update_tab_title(b))
        browser.iconChanged.connect(lambda icon, b=browser: self.update_tab_icon(icon, b))
        browser.loadProgress.connect(self.update_progress)
        # Pull context menu policies if needed, or set page settings
        if switch:
            self.tabs.setCurrentIndex(i)
        return browser

    def close_current_tab(self, i=None):
        if self.tabs.count() < 2:
            # close the window if last tab
            self.close()
            return
        if i is None:
            i = self.tabs.currentIndex()
        self.tabs.removeTab(i)

    def current_browser(self):
        return self.tabs.currentWidget()

    def current_tab_changed(self, i):
        q = self.current_browser().url()
        self.update_urlbar(q, self.current_browser())

    def update_tab_title(self, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            title = browser.title() or browser.url().toString()
            self.tabs.setTabText(index, title)

    def update_tab_icon(self, icon, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabIcon(index, icon)

    # ----------------- Navigation -----------------
    def navigate_home(self):
        self.current_browser().setUrl(QUrl(HOME_PAGE))

    def navigate_to_url_from_bar(self):
        url_text = self.urlbar.text().strip()
        if not url_text:
            return
        # Basic heuristic: if no scheme, assume http(s)
        if "://" not in url_text:
            url_text = "http://" + url_text
        q = QUrl(url_text)
        if q.isValid():
            self.current_browser().setUrl(q)

    def update_urlbar(self, q, browser=None):
        if browser != self.current_browser():
            # ignore signals from background tabs
            return
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)
        self.status.showMessage(q.toString())

    def update_progress(self, p):
        self.status.showMessage(f"Loading... {p}%")
        if p == 100:
            self.status.clearMessage()

    # ----------------- Bookmarks -----------------
    def load_bookmarks(self):
        if not os.path.exists(BOOKMARKS_FILE):
            self.bookmarks = []
            return
        try:
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                self.bookmarks = json.load(f)
        except Exception:
            self.bookmarks = []

    def save_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def refresh_bookmarks_menu(self):
        # Remove dynamic bookmark actions (keep first two entries: Manage and separator)
        # Rebuild after the first two fixed items
        actions = self.bookmarks_menu.actions()
        # Remove actions after the first two
        for a in actions[2:]:
            self.bookmarks_menu.removeAction(a)

        if not self.bookmarks:
            a = self.bookmarks_menu.addAction("(no bookmarks)")
            a.setEnabled(False)
            return

        for bm in self.bookmarks:
            title = bm.get("title") or bm.get("url")
            url = bm.get("url")
            act = QAction(title, self)
            act.triggered.connect(lambda checked, u=url: self.add_new_tab(u, switch=True))
            self.bookmarks_menu.addAction(act)

    def add_bookmark_for_current_page(self):
        browser = self.current_browser()
        if not browser:
            return
        url = browser.url().toString()
        title = browser.title() or url
        # avoid duplicates
        if any(b.get("url") == url for b in self.bookmarks):
            QMessageBox.information(self, "Bookmark", "This page is already bookmarked.")
            return
        self.bookmarks.append({"title": title, "url": url})
        self.save_bookmarks()
        self.refresh_bookmarks_menu()
        QMessageBox.information(self, "Bookmark", f"Bookmarked: {title}")

    def manage_bookmarks(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Manage Bookmarks")
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)
        listw = QtWidgets.QListWidget()
        for bm in self.bookmarks:
            listw.addItem(f"{bm.get('title')} — {bm.get('url')}")
        layout.addWidget(listw)
        btn_layout = QtWidgets.QHBoxLayout()
        remove_btn = QtWidgets.QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self._remove_selected_bookmark(listw))
        btn_layout.addWidget(remove_btn)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        dlg.exec_()
        self.save_bookmarks()
        self.refresh_bookmarks_menu()

    def _remove_selected_bookmark(self, listw):
        idx = listw.currentRow()
        if idx >= 0 and idx < len(self.bookmarks):
            del self.bookmarks[idx]
            listw.takeItem(idx)

    # ----------------- File / Page Actions -----------------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "HTML files (*.htm *.html);;All files (*.*)")
        if path:
            url = QUrl.fromLocalFile(path)
            self.add_new_tab(url.toString(), switch=True)

    def save_page(self):
        # Basic save: get current page HTML and save to file
        browser = self.current_browser()
        if not browser:
            return
        def callback(html):
            path, _ = QFileDialog.getSaveFileName(self, "Save Page As", "", "HTML files (*.html);;All files (*.*)")
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(html)
                    QMessageBox.information(self, "Save", f"Saved to {path}")
                except Exception as e:
                    QMessageBox.warning(self, "Save", f"Could not save: {e}")
        browser.page().toHtml(callback)

    # ----------------- Utility -----------------
    def focus_urlbar(self):
        """Focus and select the URL bar (used by Ctrl+L)."""
        if self.urlbar:
            self.urlbar.setFocus()
            self.urlbar.selectAll()

    # ----------------- Close Event -----------------
    def closeEvent(self, event):
        # Confirm exit
        reply = QMessageBox.question(self, "Quit", "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    # Set High DPI attributes BEFORE creating the QApplication
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()




