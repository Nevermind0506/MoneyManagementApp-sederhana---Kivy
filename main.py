# Tidak berubah: semua import sama
import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle




class TransactionHistory(GridLayout):
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

class TransactionCard(BoxLayout):
    def __init__(self, transaction, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=110, padding=12, spacing=6, **kwargs)

        ttype = transaction.get('type', '')
        amount = transaction.get('amount', 0)
        desc = transaction.get('description', '')
        date_str = transaction.get('date', '')[:19].replace('T', ' ')
        is_income = ttype == 'income'

        # Warna background dan teks
        color_bg = get_color_from_hex("#d1fae5") if is_income else get_color_from_hex("#fee2e2")
        color_text = get_color_from_hex("#064e3b") if is_income else get_color_from_hex("#7f1d1d")

        # Background card bulat
        with self.canvas.before:
            Color(rgba=color_bg)
            self.rect = RoundedRectangle(radius=[10], size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Tipe transaksi
        title = "🟢 Pemasukan" if is_income else "🔴 Pengeluaran"
        lbl_title = Label(text=title, color=color_text, bold=True, font_size=16,
                          size_hint_y=None, height=22, halign='left', valign='middle')
        lbl_title.bind(size=lbl_title.setter('text_size'))
        self.add_widget(lbl_title)

        # Tanggal
        lbl_date = Label(text=f"Tanggal     : {date_str}", color=color_text,
                         size_hint_y=None, height=20, halign='left', valign='middle')
        lbl_date.bind(size=lbl_date.setter('text_size'))
        self.add_widget(lbl_date)

        # Jumlah
        lbl_amount = Label(text=f"Jumlah      : Rp {amount:,.0f}", color=color_text,
                           size_hint_y=None, height=20, halign='left', valign='middle')
        lbl_amount.bind(size=lbl_amount.setter('text_size'))
        self.add_widget(lbl_amount)

        # Keterangan
        lbl_desc = Label(text=f"Keterangan  : {desc}", color=color_text,
                         size_hint_y=None, height=20, halign='left', valign='middle')
        lbl_desc.bind(size=lbl_desc.setter('text_size'))
        self.add_widget(lbl_desc)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class FinanceTrackerApp(App):
    def build(self):
        self.title = "Pencatat Keuangan Harian"
        Window.size = (400, 700)

        self.transactions_file = "transactions.json"
        self.transactions = []
        self.filtered_transactions = []
        self.balance = 0.0

        root_layout = BoxLayout(orientation='vertical', padding=16, spacing=12)

        # === Input Pemasukan ===
        root_layout.add_widget(Label(text='Input Pemasukan:', size_hint_y=None, height=24, bold=True))
        income_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        self.income_amount = TextInput(hint_text='Jumlah (misal: 50000)', multiline=False, input_filter='int')
        self.income_desc = TextInput(hint_text='Keterangan', multiline=False)
        income_box.add_widget(self.income_amount)
        income_box.add_widget(self.income_desc)
        root_layout.add_widget(income_box)

        # === Input Pengeluaran ===
        root_layout.add_widget(Label(text='Input Pengeluaran:', size_hint_y=None, height=24, bold=True))
        expense_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        self.expense_amount = TextInput(hint_text='Jumlah (misal: 15000)', multiline=False, input_filter='int')
        self.expense_desc = TextInput(hint_text='Keterangan', multiline=False)
        expense_box.add_widget(self.expense_amount)
        expense_box.add_widget(self.expense_desc)
        root_layout.add_widget(expense_box)

        # === Tombol Pemasukan / Pengeluaran ===
        buttons_box = BoxLayout(size_hint_y=None, height=45, spacing=12)
        btn_add_income = Button(text='+ Pemasukan', background_color=get_color_from_hex('#10b981'))
        btn_add_income.bind(on_press=self.add_income)
        btn_add_expense = Button(text='- Pengeluaran', background_color=get_color_from_hex('#ef4444'))
        btn_add_expense.bind(on_press=self.add_expense)
        buttons_box.add_widget(btn_add_income)
        buttons_box.add_widget(btn_add_expense)
        root_layout.add_widget(buttons_box)

        # === Saldo ===
        self.balance_label = Label(text='Saldo Saat Ini: Rp 0', font_size=22, size_hint_y=None, height=40, bold=True, color=[1,1,1,1])
        root_layout.add_widget(self.balance_label)

        # === Riwayat Transaksi ===
        root_layout.add_widget(Label(text='Riwayat Transaksi:', size_hint_y=None, height=24, bold=True))
        # === Pencarian Riwayat ===
        search_box = BoxLayout(size_hint_y=None, height=40)
        self.search_input = TextInput(hint_text='Cari transaksi (misal: jajan)', multiline=False)
        self.search_input.bind(text=self.on_search_text)
        search_box.add_widget(self.search_input)
        root_layout.add_widget(Label(text='Pencarian:', size_hint_y=None, height=24))
        root_layout.add_widget(search_box)


        self.history = TransactionHistory()
        scroll = ScrollView(size_hint=(1, 1))
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
        self.balance_label.text = f"Saldo Saat Ini: Rp {self.balance:,.0f}"

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
        for transaction in reversed(data):  # terbaru di atas
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
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        btn = Button(text='Tutup', size_hint_y=None, height=40)
        content.add_widget(btn)
        popup = Popup(title='Kesalahan', content=content, size_hint=(None, None), size=(300, 200))
        btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    FinanceTrackerApp().run()
