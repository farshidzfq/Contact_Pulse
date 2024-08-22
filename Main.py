import sys
import sqlite3
import re
import csv
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QTabWidget, 
                             QFormLayout, QComboBox, QFileDialog, QMessageBox)

class AddressBook(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("دفترچه آدرس")
        self.setGeometry(100, 100, 1000, 600)  # افزایش اندازه پنجره برای جدول
        self.initialize_database()
        self.create_connection()
        self.selected_contact_id = None

        self.tabs = QTabWidget()
        self.add_tab = QWidget()
        self.view_tab = QWidget()

        self.tabs.addTab(self.add_tab, "اضافه کردن مخاطب")
        self.tabs.addTab(self.view_tab, "مشاهده و جستجو")

        self.create_add_tab()
        self.create_view_tab()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)

    def initialize_database(self):
        if os.path.exists('contacts.db'):
            os.remove('contacts.db')

        conn = sqlite3.connect('contacts.db')
        c = conn.cursor()

        c.execute('''
            CREATE TABLE contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                group_name TEXT
            )
        ''')

        c.execute('''
            CREATE TABLE phone_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                phone TEXT,
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )
        ''')

        c.execute('''
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                email TEXT,
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_connection(self):
        self.conn = sqlite3.connect('contacts.db')
        self.c = self.conn.cursor()

    def create_add_tab(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.address_input = QLineEdit()

        self.group_input = QComboBox()
        self.group_input.addItems(["خانواده", "دوستان", "همکاران", "دیگر"])

        self.phone_input = QLineEdit()
        self.phone_list = QTableWidget()
        self.phone_list.setColumnCount(1)
        self.phone_list.setHorizontalHeaderLabels(['شماره تلفن'])
        self.add_phone_button = QPushButton("اضافه کردن شماره تلفن")
        self.add_phone_button.clicked.connect(self.add_phone)

        self.email_input = QLineEdit()
        self.email_list = QTableWidget()
        self.email_list.setColumnCount(1)
        self.email_list.setHorizontalHeaderLabels(['ایمیل'])
        self.add_email_button = QPushButton("اضافه کردن ایمیل")
        self.add_email_button.clicked.connect(self.add_email)

        form_layout.addRow("نام:", self.name_input)
        form_layout.addRow("آدرس:", self.address_input)
        form_layout.addRow("گروه:", self.group_input)
        form_layout.addRow("شماره تلفن:", self.phone_input)
        form_layout.addRow("", self.add_phone_button)
        form_layout.addRow("", self.phone_list)
        form_layout.addRow("ایمیل:", self.email_input)
        form_layout.addRow("", self.add_email_button)
        form_layout.addRow("", self.email_list)

        self.add_button = QPushButton("اضافه کردن مخاطب")
        self.add_button.clicked.connect(self.add_contact)

        layout.addLayout(form_layout)
        layout.addWidget(self.add_button)
        self.add_tab.setLayout(layout)

    def create_view_tab(self):
        layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجوی مخاطب...")
        self.search_input.textChanged.connect(self.search_contact)

        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(6)  # اضافه کردن ستون برای شماره تلفن و ایمیل
        self.contact_table.setHorizontalHeaderLabels(['نام', 'آدرس', 'گروه', 'شماره تلفن', 'ایمیل', 'شناسه'])
        self.contact_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contact_table.itemSelectionChanged.connect(self.display_contact)

        self.edit_button = QPushButton("ویرایش")
        self.edit_button.clicked.connect(self.edit_contact)
        self.delete_button = QPushButton("حذف")
        self.delete_button.clicked.connect(self.delete_contact)
        self.export_button = QPushButton("خروجی به CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.merge_button = QPushButton("ادغام مخاطبین مشابه")
        self.merge_button.clicked.connect(self.merge_contacts)

        layout.addWidget(self.search_input)
        layout.addWidget(self.contact_table)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.merge_button)

        self.view_tab.setLayout(layout)
        self.update_contact_list()

    def is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email)

    def is_valid_phone(self, phone):
        pattern = r'^\+?[\d\s\-]{7,15}$'
        return re.match(pattern, phone)

    def add_contact(self):
        name = self.name_input.text()
        address = self.address_input.text()
        group = self.group_input.currentText()

        if not name:
            QMessageBox.warning(self, "خطا", "لطفاً نام را وارد کنید.")
            return

        self.c.execute("INSERT INTO contacts (name, address, group_name) VALUES (?, ?, ?)",
                       (name, address, group))
        contact_id = self.c.lastrowid

        for i in range(self.phone_list.rowCount()):
            phone = self.phone_list.item(i, 0).text()
            if not self.is_valid_phone(phone):
                QMessageBox.warning(self, "خطا", "شماره تلفن معتبر نیست.")
                return
            self.c.execute("INSERT INTO phone_numbers (contact_id, phone) VALUES (?, ?)", (contact_id, phone))

        for i in range(self.email_list.rowCount()):
            email = self.email_list.item(i, 0).text()
            if not self.is_valid_email(email):
                QMessageBox.warning(self, "خطا", "ایمیل معتبر نیست.")
                return
            self.c.execute("INSERT INTO emails (contact_id, email) VALUES (?, ?)", (contact_id, email))

        self.conn.commit()
        self.update_contact_list()
        self.clear_inputs()

    def add_phone(self):
        phone = self.phone_input.text()
        if self.is_valid_phone(phone):
            row_position = self.phone_list.rowCount()
            self.phone_list.insertRow(row_position)
            self.phone_list.setItem(row_position, 0, QTableWidgetItem(phone))
            self.phone_input.clear()
        else:
            QMessageBox.warning(self, "خطا", "شماره تلفن وارد شده معتبر نیست.")

    def add_email(self):
        email = self.email_input.text()
        if self.is_valid_email(email):
            row_position = self.email_list.rowCount()
            self.email_list.insertRow(row_position)
            self.email_list.setItem(row_position, 0, QTableWidgetItem(email))
            self.email_input.clear()
        else:
            QMessageBox.warning(self, "خطا", "ایمیل وارد شده معتبر نیست.")

    def clear_inputs(self):
        self.name_input.clear()
        self.address_input.clear()
        self.group_input.setCurrentIndex(0)
        self.phone_list.setRowCount(0)
        self.email_list.setRowCount(0)

    def update_contact_list(self):
        self.contact_table.setRowCount(0)
        self.c.execute('''
            SELECT c.id, c.name, c.address, c.group_name, 
                   GROUP_CONCAT(DISTINCT p.phone), 
                   GROUP_CONCAT(DISTINCT e.email)
            FROM contacts c
            LEFT JOIN phone_numbers p ON c.id = p.contact_id
            LEFT JOIN emails e ON c.id = e.contact_id
            GROUP BY c.id
        ''')

        for row in self.c.fetchall():
            row_position = self.contact_table.rowCount()
            self.contact_table.insertRow(row_position)
            self.contact_table.setItem(row_position, 0, QTableWidgetItem(row[1]))  # نام
            self.contact_table.setItem(row_position, 1, QTableWidgetItem(row[2]))  # آدرس
            self.contact_table.setItem(row_position, 2, QTableWidgetItem(row[3]))  # گروه
            self.contact_table.setItem(row_position, 3, QTableWidgetItem(row[4] if row[4] else ''))  # شماره تلفن
            self.contact_table.setItem(row_position, 4, QTableWidgetItem(row[5] if row[5] else ''))  # ایمیل
            self.contact_table.setItem(row_position, 5, QTableWidgetItem(str(row[0])))  # شناسه

    def display_contact(self):
        selected_row = self.contact_table.currentRow()
        if selected_row >= 0:
            self.selected_contact_id = int(self.contact_table.item(selected_row, 5).text())
            self.c.execute("SELECT name, address, group_name FROM contacts WHERE id=?", (self.selected_contact_id,))
            contact = self.c.fetchone()
            if contact:
                self.name_input.setText(contact[0])
                self.address_input.setText(contact[1])
                self.group_input.setCurrentText(contact[2])

                self.phone_list.setRowCount(0)
                self.c.execute("SELECT phone FROM phone_numbers WHERE contact_id=?", (self.selected_contact_id,))
                for phone in self.c.fetchall():
                    row_position = self.phone_list.rowCount()
                    self.phone_list.insertRow(row_position)
                    self.phone_list.setItem(row_position, 0, QTableWidgetItem(phone[0]))

                self.email_list.setRowCount(0)
                self.c.execute("SELECT email FROM emails WHERE contact_id=?", (self.selected_contact_id,))
                for email in self.c.fetchall():
                    row_position = self.email_list.rowCount()
                    self.email_list.insertRow(row_position)
                    self.email_list.setItem(row_position, 0, QTableWidgetItem(email[0]))

    def edit_contact(self):
        if self.selected_contact_id is None:
            QMessageBox.warning(self, "خطا", "لطفاً یک مخاطب را انتخاب کنید.")
            return

        name = self.name_input.text()
        address = self.address_input.text()
        group = self.group_input.currentText()

        if not name:
            QMessageBox.warning(self, "خطا", "لطفاً نام را وارد کنید.")
            return

        self.c.execute("UPDATE contacts SET name=?, address=?, group_name=? WHERE id=?",
                       (name, address, group, self.selected_contact_id))

        self.c.execute("DELETE FROM phone_numbers WHERE contact_id=?", (self.selected_contact_id,))
        for i in range(self.phone_list.rowCount()):
            phone = self.phone_list.item(i, 0).text()
            if self.is_valid_phone(phone):
                self.c.execute("INSERT INTO phone_numbers (contact_id, phone) VALUES (?, ?)",
                               (self.selected_contact_id, phone))

        self.c.execute("DELETE FROM emails WHERE contact_id=?", (self.selected_contact_id,))
        for i in range(self.email_list.rowCount()):
            email = self.email_list.item(i, 0).text()
            if self.is_valid_email(email):
                self.c.execute("INSERT INTO emails (contact_id, email) VALUES (?, ?)",
                               (self.selected_contact_id, email))

        self.conn.commit()
        self.update_contact_list()
        self.clear_inputs()
        QMessageBox.information(self, "ویرایش موفق", "مخاطب با موفقیت ویرایش شد.")
        self.selected_contact_id = None

    def delete_contact(self):
        if self.selected_contact_id is None:
            QMessageBox.warning(self, "خطا", "لطفاً یک مخاطب را انتخاب کنید.")
            return

        confirm = QMessageBox.question(self, "تأیید حذف", "آیا مطمئن هستید که می‌خواهید این مخاطب را حذف کنید؟",
                                       QMessageBox.Yes | QMessageBox.No)

        if confirm == QMessageBox.Yes:
            self.c.execute("DELETE FROM contacts WHERE id=?", (self.selected_contact_id,))
            self.c.execute("DELETE FROM phone_numbers WHERE contact_id=?", (self.selected_contact_id,))
            self.c.execute("DELETE FROM emails WHERE contact_id=?", (self.selected_contact_id,))
            self.conn.commit()
            self.update_contact_list()
            self.clear_inputs()
            QMessageBox.information(self, "حذف موفق", "مخاطب با موفقیت حذف شد.")
            self.selected_contact_id = None

    def search_contact(self, text):
        self.contact_table.setRowCount(0)
        self.c.execute('''
            SELECT c.id, c.name, c.address, c.group_name, 
                   GROUP_CONCAT(DISTINCT p.phone), 
                   GROUP_CONCAT(DISTINCT e.email)
            FROM contacts c
            LEFT JOIN phone_numbers p ON c.id = p.contact_id
            LEFT JOIN emails e ON c.id = e.contact_id
            WHERE c.name LIKE ?
            GROUP BY c.id
        ''', ('%' + text + '%',))
        for row in self.c.fetchall():
            row_position = self.contact_table.rowCount()
            self.contact_table.insertRow(row_position)
            self.contact_table.setItem(row_position, 0, QTableWidgetItem(row[1]))  # نام
            self.contact_table.setItem(row_position, 1, QTableWidgetItem(row[2]))  # آدرس
            self.contact_table.setItem(row_position, 2, QTableWidgetItem(row[3]))  # گروه
            self.contact_table.setItem(row_position, 3, QTableWidgetItem(row[4] if row[4] else ''))  # شماره تلفن
            self.contact_table.setItem(row_position, 4, QTableWidgetItem(row[5] if row[5] else ''))  # ایمیل
            self.contact_table.setItem(row_position, 5, QTableWidgetItem(str(row[0])))  # شناسه

    def merge_contacts(self):
        self.c.execute('''
            SELECT name, GROUP_CONCAT(DISTINCT id), COUNT(*)
            FROM contacts
            GROUP BY name
            HAVING COUNT(*) > 1
        ''')
        duplicates = self.c.fetchall()

        for name, ids, count in duplicates:
            id_list = ids.split(',')
            main_id = id_list[0]

            for other_id in id_list[1:]:
                self.c.execute('''
                    UPDATE phone_numbers SET contact_id = ?
                    WHERE contact_id = ?
                ''', (main_id, other_id))

                self.c.execute('''
                    UPDATE emails SET contact_id = ?
                    WHERE contact_id = ?
                ''', (main_id, other_id))

                self.c.execute('DELETE FROM contacts WHERE id = ?', (other_id,))

        self.conn.commit()
        self.update_contact_list()
        QMessageBox.information(self, "ادغام مخاطبین", "مخاطبین مشابه با موفقیت ادغام شدند.")

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "ذخیره به عنوان CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        self.c.execute('''
            SELECT c.name, c.address, c.group_name, 
                   GROUP_CONCAT(DISTINCT p.phone), 
                   GROUP_CONCAT(DISTINCT e.email)
            FROM contacts c
            LEFT JOIN phone_numbers p ON c.id = p.contact_id
            LEFT JOIN emails e ON c.id = e.contact_id
            GROUP BY c.id
        ''')

        rows = self.c.fetchall()

        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['نام', 'آدرس', 'گروه', 'شماره تلفن‌ها', 'ایمیل‌ها'])
            writer.writerows(rows)

        QMessageBox.information(self, "خروجی CSV", "مخاطبین با موفقیت به CSV صادر شدند.")

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AddressBook()
    window.show()
    sys.exit(app.exec_())
