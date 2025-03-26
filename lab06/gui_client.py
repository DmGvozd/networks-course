import sys
from ftplib import FTP, error_perm
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QListWidget, QTextEdit, 
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt

class FTPClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ftp = None
        
        self.setWindowTitle("FTP Client")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        
        self.connection_layout = QHBoxLayout()
        
        self.label_host = QLabel("FTP Host:")
        self.input_host = QLineEdit()
        self.input_host.setText("ftp.dlptest.com")
        
        self.label_port = QLabel("Port:")
        self.input_port = QLineEdit()
        self.input_port.setText("21")
        
        self.label_user = QLabel("User:")
        self.input_user = QLineEdit()
        
        self.label_password = QLabel("Password:")
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        
        self.button_connect = QPushButton("Connect")
        self.button_connect.clicked.connect(self.connect_ftp)
        
        self.connection_layout.addWidget(self.label_host)
        self.connection_layout.addWidget(self.input_host)
        self.connection_layout.addWidget(self.label_port)
        self.connection_layout.addWidget(self.input_port)
        self.connection_layout.addWidget(self.label_user)
        self.connection_layout.addWidget(self.input_user)
        self.connection_layout.addWidget(self.label_password)
        self.connection_layout.addWidget(self.input_password)
        self.connection_layout.addWidget(self.button_connect)
        
        self.main_layout.addLayout(self.connection_layout)
        
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.retrieve_file)
        self.main_layout.addWidget(self.file_list)
        
        self.text_content = QTextEdit()
        self.main_layout.addWidget(self.text_content)
        
        self.buttons_layout = QHBoxLayout()
        self.button_create = QPushButton("Create File")
        self.button_create.clicked.connect(self.create_file)
        
        self.button_retrieve = QPushButton("Retrieve File")
        self.button_retrieve.clicked.connect(self.retrieve_file)
        
        self.button_update = QPushButton("Update File")
        self.button_update.clicked.connect(self.update_file)
        
        self.button_delete = QPushButton("Delete File")
        self.button_delete.clicked.connect(self.delete_file)
        
        self.buttons_layout.addWidget(self.button_create)
        self.buttons_layout.addWidget(self.button_retrieve)
        self.buttons_layout.addWidget(self.button_update)
        self.buttons_layout.addWidget(self.button_delete)
        
        self.main_layout.addLayout(self.buttons_layout)

    def connect_ftp(self):
        host = self.input_host.text()
        port = int(self.input_port.text())
        user = self.input_user.text()
        password = self.input_password.text()
        
        try:
            if self.ftp is not None:
                self.ftp.quit()
        except:
            pass
        
        try:
            self.ftp = FTP()
            self.ftp.connect(host, port, timeout=5)
            self.ftp.login(user, password)
            
            QMessageBox.information(self, "Success", "Connected to FTP server")
            self.refresh_file_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed!\n{e}")
            self.ftp = None

    def refresh_file_list(self):
        if not self.ftp:
            return
        
        self.file_list.clear()
        
        try:
            items = []
            self.ftp.retrlines("LIST", items.append)
            for line in items:
                parts = line.split(None, 8)
                if len(parts) < 9:
                    continue
                filename = parts[-1]
                self.file_list.addItem(filename)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list files!\n{e}")

    def retrieve_file(self):
        if not self.ftp:
            QMessageBox.warning(self, "Warning", "Not connected to FTP server!")
            return
        
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "No file selected!")
            return
        
        filename = item.text()
        
        try:
            content_lines = []
            self.ftp.retrlines(f"RETR {filename}", content_lines.append)
            content = "\n".join(content_lines)
            self.text_content.setPlainText(content)
        except error_perm as e:
            QMessageBox.critical(self, "Error", f"Cannot retrieve file!\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error retrieving file!\n{e}")

    def create_file(self):
        if not self.ftp:
            QMessageBox.warning(self, "Warning", "Not connected to FTP server!")
            return
        
        dialog = FileNameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.file_name.text().strip()
            if not filename:
                QMessageBox.warning(self, "Warning", "Filename cannot be empty!")
                return
            content_dialog = FileContentDialog(self, title="Create File")
            if content_dialog.exec_() == QDialog.Accepted:
                content = content_dialog.text_editor.toPlainText()
                self.upload_content(filename, content, is_new=True)

    def update_file(self):
        if not self.ftp:
            QMessageBox.warning(self, "Warning", "Not connected to FTP server!")
            return
        
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "No file selected!")
            return
        
        filename = item.text()
        
        try:
            content_lines = []
            self.ftp.retrlines(f"RETR {filename}", content_lines.append)
            old_content = "\n".join(content_lines)
        except:
            old_content = ""
        
        content_dialog = FileContentDialog(self, title=f"Update File: {filename}")
        content_dialog.text_editor.setPlainText(old_content)
        
        if content_dialog.exec_() == QDialog.Accepted:
            new_content = content_dialog.text_editor.toPlainText()
            self.upload_content(filename, new_content, is_new=False)

    def upload_content(self, filename, content, is_new=True):
        from io import BytesIO
        bio = BytesIO(content.encode('utf-8'))
        
        try:
            self.ftp.storbinary(f"STOR {filename}", bio)
            if is_new:
                QMessageBox.information(self, "Success", f"File '{filename}' created successfully!")
            else:
                QMessageBox.information(self, "Success", f"File '{filename}' updated successfully!")
            self.refresh_file_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Upload failed!\n{e}")

    def delete_file(self):
        if not self.ftp:
            QMessageBox.warning(self, "Warning", "Not connected to FTP server!")
            return
        
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "No file selected!")
            return
        
        filename = item.text()
        
        reply = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete '{filename}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.ftp.delete(filename)
                QMessageBox.information(self, "Success", f"File '{filename}' deleted successfully!")
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed!\n{e}")


class FileNameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Name")
        
        layout = QFormLayout(self)
        self.file_name = QLineEdit()
        layout.addRow("Enter file name:", self.file_name)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class FileContentDialog(QDialog):
    def __init__(self, parent=None, title="File Content"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)
        
        main_layout = QVBoxLayout(self)
        
        self.text_editor = QTextEdit()
        main_layout.addWidget(self.text_editor)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)


def main():
    app = QApplication(sys.argv)
    window = FTPClientWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
