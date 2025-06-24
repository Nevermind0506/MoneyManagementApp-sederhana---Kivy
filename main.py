
import json
import os
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle

class TransactionHistory(MDGridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.size_hint_y = None
        self.spacing = 6
        self.padding = [8, 8, 8, 8]
        self.bind(minimum_height=self.setter('height'))

    def add_transaction(self, transaction):
        card = TransactionCard(transaction)
        self.add_widget(card)

class TransactionCard(MDBoxLayout):
    def __init__(self, transaction, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=110, padding=12, spacing=6, **kwargs)

        ttype = transaction.get('type', '')
        amount = transaction.get('amount', 0)
        desc = transaction.get('description', '')
        date_str = transaction.get('date', '')[:19].replace('T', ' ')
        is_income = ttype == 'income'

        color_bg = get_color_from_hex("#d1fae5") if is_income else get_color_from_hex("#fee2e2")
        color_text = get_color_from_hex("#064e3b") if is_income else get_color_from_hex("#7f1d1d")

        with self.canvas.before:
            Color(rgba=color_bg)
            self.rect = RoundedRectangle(radius=[10], size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        title = "🟢 Pemasukan" if is_income else "🔴 Pengeluaran"
        lbl_title = MDLabel(text=title, theme_text_color="Custom", text_color=color_text, bold=True, font_style="H6",
                            size_hint_y=None, height=22, halign='left', valign='middle')
        lbl_title.bind(size=lbl_title.setter('text_size'))
        self.add_widget(lbl_title)

        lbl_date = MDLabel(text=f"📅 Tanggal     : {date_str}", theme_text_color="Custom", text_color=color_text,
                           size_hint_y=None, height=20, halign='left', valign='middle')
        lbl_date.bind(size=lbl_date.setter('text_size'))
        self.add_widget(lbl_date)

        lbl_amount = MDLabel(text=f"💵 Jumlah      : Rp {amount:,.0f}", theme_text_color="Custom", text_color=color_text,
                             size_hint_y=None, height=20, halign='left', valign='middle')
        lbl_amount.bind(size=lbl_amount.setter('text_size'))
        self.add_widget(lbl_amount)

        lbl_desc = MDLabel(text=f"📝 Keterangan  : {desc}", theme_text_color="Custom", text_color=color_text,
                           size_hint_y=None, height=20, halign='left', valign='middle')
        lbl_desc.bind(size=lbl_desc.setter('text_size'))
        self.add_widget(lbl_desc)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class InputCard(MDBoxLayout):
    def __init__(self, title, amount_input, desc_input, button, bg_color="#f3f4f6", **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=140, padding=12, spacing=8, **kwargs)

        with self.canvas.before:
            Color(rgba=get_color_from_hex(bg_color))
            self.rect = RoundedRectangle(radius=[12], size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        lbl = MDLabel(text=title, size_hint_y=None, height=24, bold=True, theme_text_color="Custom",
                      text_color=[0.1, 0.1, 0.1, 1], halign='left')
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)

        form_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        form_row.add_widget(amount_input)
        form_row.add_widget(desc_input)
        self.add_widget(form_row)

        self.add_widget(button)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class FinanceTrackerApp(MDApp):
    def build(self):
        self.title = "Pencatat Keuangan Harian"
        Window.size = (400, 700)

        self.transactions_file = "transactions.json"
        self.transactions = []
        self.filtered_transactions = []
        self.balance = 0.0

        root_layout = MDBoxLayout(orientation='vertical', padding=[16, 20, 16, 20], spacing=16)

        # Input Pemasukan
        self.income_amount = MDTextField(hint_text='Input Pemasukan', input_filter='int', mode="rectangle")
        self.income_desc = MDTextField(hint_text='Keterangan', mode="rectangle")
        btn_add_income = MDRaisedButton(text='➕ Tambah Pemasukan', md_bg_color=get_color_from_hex('#10b981'), text_color=[1,1,1,1])
        btn_add_income.bind(on_press=self.add_income)
        income_card = InputCard("", self.income_amount, self.income_desc, btn_add_income, bg_color="#e0f7f0")
        root_layout.add_widget(income_card)

        # Input Pengeluaran
        self.expense_amount = MDTextField(hint_text='Input Pengeluaran', input_filter='int', mode="rectangle")
        self.expense_desc = MDTextField(hint_text='Keterangan', mode="rectangle")
        btn_add_expense = MDRaisedButton(text='➖ Tambah Pengeluaran', md_bg_color=get_color_from_hex('#ef4444'), text_color=[1,1,1,1])
        btn_add_expense.bind(on_press=self.add_expense)
        expense_card = InputCard("", self.expense_amount, self.expense_desc, btn_add_expense, bg_color="#fcebea")
        root_layout.add_widget(expense_card)

        # Saldo
        self.balance_label = MDLabel(text='💰 Saldo Saat Ini: Rp 0', font_style="H5", size_hint_y=None, height=40, bold=True, theme_text_color="Custom", text_color=[0,0,0,1])
        root_layout.add_widget(self.balance_label)

        # Riwayat Transaksi
        root_layout.add_widget(MDLabel(text='Riwayat Transaksi:', size_hint_y=None, height=24, bold=True, theme_text_color="Primary"))

        # Pencarian Riwayat
        search_box = MDBoxLayout(size_hint_y=None, height=40)
        self.search_input = MDTextField(hint_text='Cari transaksi (misal: jajan)', mode="rectangle")
        self.search_input.bind(text=self.on_search_text)
        search_box.add_widget(self.search_input)
        root_layout.add_widget(MDLabel(text='', size_hint_y=None, height=24, bold=True, theme_text_color="Primary"))
        root_layout.add_widget(search_box)

        self.history = TransactionHistory()
        scroll = MDScrollView(size_hint=(1, 1))
        scroll.add_widget(self.history)
        root_layout.add_widget(scroll)

        self.load_transactions()
        self.filtered_transactions = self.transactions.copy()
        self.update_balance_label()
        self.populate_history()

        return root_layout

    def add_income(self, instance):
        amount_text = self.income_amount.text.strip()
        desc_text = self.income_desc.text.strip()
        if not amount_text.isdigit() or int(amount_text) <= 0:
            self.show_error("Jumlah pemasukan harus angka positif.")
            return
        if not desc_text:
            self.show_error("Keterangan pemasukan tidak boleh kosong.")
            return
        amount = float(amount_text)
        transaction = {
            'type': 'income',
            'amount': amount,
            'description': desc_text,
            'date': datetime.now().isoformat()
        }
        self.transactions.append(transaction)
        self.balance += amount
        self.save_transactions()
        self.update_balance_label()
        self.populate_history()
        self.income_amount.text = ''
        self.income_desc.text = ''

    def add_expense(self, instance):
        amount_text = self.expense_amount.text.strip()
        desc_text = self.expense_desc.text.strip()
        if not amount_text.isdigit() or int(amount_text) <= 0:
            self.show_error("Jumlah pengeluaran harus angka positif.")
            return
        if not desc_text:
            self.show_error("Keterangan pengeluaran tidak boleh kosong.")
            return
        amount = float(amount_text)
        if amount > self.balance:
            self.show_error("Pengeluaran melebihi saldo saat ini.")
            return
        transaction = {
            'type': 'expense',
            'amount': amount,
            'description': desc_text,
            'date': datetime.now().isoformat()
        }
        self.transactions.append(transaction)
        self.balance -= amount
        self.save_transactions()
        self.update_balance_label()
        self.populate_history()
        self.expense_amount.text = ''
        self.expense_desc.text = ''

    def update_balance_label(self):
        self.balance_label.text = f"💰 Saldo Saat Ini: Rp {self.balance:,.0f}"

    def save_transactions(self):
        try:
            with open(self.transactions_file, 'w', encoding='utf-8') as f:
                json.dump(self.transactions, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.show_error(f"Gagal menyimpan transaksi: {e}")

    def load_transactions(self):
        if os.path.exists(self.transactions_file):
            try:
                with open(self.transactions_file, 'r', encoding='utf-8') as f:
                    self.transactions = json.load(f)
                self.balance = 0
                for t in self.transactions:
                    if t.get('type') == 'income':
                        self.balance += t.get('amount', 0)
                    elif t.get('type') == 'expense':
                        self.balance -= t.get('amount', 0)
            except Exception as e:
                self.show_error(f"Gagal memuat data transaksi: {e}")
                self.transactions = []
                self.balance = 0

    def populate_history(self, filtered=False):
        self.history.clear_widgets()
        data = self.filtered_transactions if filtered else self.transactions
        for transaction in reversed(data):
            self.history.add_transaction(transaction)
    
    def on_search_text(self, instance, value):
        keyword = value.strip().lower()
        if keyword == "":
            self.filtered_transactions = self.transactions
        else:
            self.filtered_transactions = [
                t for t in self.transactions
                if keyword in t.get("description", "").lower()
                or keyword in t.get("type", "").lower()
                or keyword in str(t.get("amount", "")).lower()
            ]
        self.populate_history(filtered=True)

    def show_error(self, message):
        content = MDBoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(MDLabel(text=message, theme_text_color="Error"))
        btn = MDRaisedButton(text='Tutup', md_bg_color=get_color_from_hex('#ef4444'), text_color=[1,1,1,1], size_hint_y=None, height=40)
        content.add_widget(btn)
        popup = Popup(title='Kesalahan', content=content, size_hint=(None, None), size=(300, 200))
        btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    FinanceTrackerApp().run()
