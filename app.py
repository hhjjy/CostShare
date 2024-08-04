import streamlit as st
import pandas as pd
from datetime import date
import json
import os

# JSON 文件路徑
JSON_FILE = "bills.json"

# 從 JSON 文件讀取數據
def load_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return {}

# 將數據保存到 JSON 文件
def save_data(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

# 初始化 session state
if 'bills' not in st.session_state:
    st.session_state.bills = load_data()
if 'page' not in st.session_state:
    st.session_state.page = 'overview'
if 'default_tax_rate' not in st.session_state:
    st.session_state.default_tax_rate = 0.08375  # 默認稅率為 8.375%

# 側邊欄導航
st.sidebar.title('導航')
if st.sidebar.button('返回總覽'):
    st.session_state.page = 'overview'

for bill_name in st.session_state.bills.keys():
    if st.sidebar.button(f'查看 {bill_name}'):
        st.session_state.page = bill_name

# 總覽頁面
def show_overview():
    st.title('總覽')
    
    # 創建新帳單
    with st.form(key='new_bill_form'):
        new_bill_name = st.text_input('新帳單名稱')
        new_bill_date = st.date_input('帳單日期', value=date.today())
        new_bill_payer = st.selectbox('付款人', ['Leo', 'Yihua', 'Cyclone', 'Vicky'])
        submitted = st.form_submit_button('創建新帳單')
        if submitted and new_bill_name and new_bill_name not in st.session_state.bills:
            st.session_state.bills[new_bill_name] = {
                'date': new_bill_date.isoformat(),
                'payer': new_bill_payer,
                'expenses': []
            }
            save_data(st.session_state.bills)
            st.success(f'已創建新帳單：{new_bill_name}')
            st.session_state.page = new_bill_name

    # 顯示所有帳單摘要
    if st.session_state.bills:
        summary_data = []
        for bill_name, bill_data in st.session_state.bills.items():
            total_amount = sum(expense['amount'] * (1 + expense['tax_rate']) if expense['is_taxable'] else expense['amount'] for expense in bill_data['expenses'])
            participants = set()
            participant_shares = {'Leo': 0, 'Yihua': 0, 'Cyclone': 0, 'Vicky': 0}
            
            for expense in bill_data['expenses']:
                participants.update(expense['participants'])
                amount = expense['amount'] * (1 + expense['tax_rate']) if expense['is_taxable'] else expense['amount']
                share = amount / len(expense['participants'])
                for p in expense['participants']:
                    participant_shares[p] += share
            
            summary_data.append({
                '帳單名稱': bill_name,
                '日期': bill_data['date'],
                '付款人': bill_data['payer'],
                '總金額': total_amount,
                **{f'{p} 應付': participant_shares[p] for p in ['Leo', 'Yihua', 'Cyclone', 'Vicky']}
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.write(summary_df)
        
        # 添加按鈕以進入每個帳單的詳細頁面
        for bill_name in st.session_state.bills.keys():
            if st.button(f'查看 {bill_name} 詳情'):
                st.session_state.page = bill_name
    else:
        st.write('目前沒有帳單')

# 細節帳單頁面
def show_detail_bill(bill_name):
    bill = st.session_state.bills[bill_name]
    st.title(f'細節帳單：{bill_name}')
    st.write(f"日期：{bill['date']}, 付款人：{bill['payer']}")
    
    # 添加新支出
    with st.form(key=f'expense_form_{bill_name}'):
        st.subheader('添加新支出')
        item = st.text_input('項目')
        amount = st.number_input('金額', min_value=0.0, step=0.01)
        is_taxable = st.checkbox('是否需要付稅')
        tax_rate = st.number_input('稅率', min_value=0.0, max_value=1.0, value=st.session_state.default_tax_rate, step=0.0001, format="%.4f") if is_taxable else 0
        participants = st.multiselect('參與者', ['Leo', 'Yihua', 'Cyclone', 'Vicky'])
        submitted = st.form_submit_button('添加支出')
        
        if submitted and item and amount and participants:
            new_expense = {
                'item': item,
                'amount': amount,
                'is_taxable': is_taxable,
                'tax_rate': tax_rate,
                'participants': participants
            }
            bill['expenses'].append(new_expense)
            save_data(st.session_state.bills)
            st.success('支出已添加！')

    # 顯示和編輯當前帳單的所有支出
    if bill['expenses']:
        st.subheader('編輯支出')
        for index, expense in enumerate(bill['expenses']):
            with st.expander(f"支出 {index + 1}: {expense['item']}"):
                updated_item = st.text_input(f'項目 {index}', expense['item'])
                updated_amount = st.number_input(f'金額 {index}', min_value=0.0, value=expense['amount'], step=0.01)
                updated_is_taxable = st.checkbox(f'是否需要付稅 {index}', expense['is_taxable'])
                updated_tax_rate = st.number_input(f'稅率 {index}', min_value=0.0, max_value=1.0, value=expense['tax_rate'], step=0.0001, format="%.4f") if updated_is_taxable else 0
                updated_participants = st.multiselect(f'參與者 {index}', ['Leo', 'Yihua', 'Cyclone', 'Vicky'], default=expense['participants'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f'更新支出 {index}'):
                        bill['expenses'][index] = {
                            'item': updated_item,
                            'amount': updated_amount,
                            'is_taxable': updated_is_taxable,
                            'tax_rate': updated_tax_rate,
                            'participants': updated_participants
                        }
                        save_data(st.session_state.bills)
                        st.success('支出已更新！')
                with col2:
                    if st.button(f'刪除支出 {index}'):
                        del bill['expenses'][index]
                        save_data(st.session_state.bills)
                        st.success('支出已刪除！')

        # 顯示支出摘要
        expense_data = []
        total_amount = 0
        participant_shares = {'Leo': 0, 'Yihua': 0, 'Cyclone': 0, 'Vicky': 0}

        for e in bill['expenses']:
            amount_with_tax = e['amount'] * (1 + e['tax_rate']) if e['is_taxable'] else e['amount']
            total_amount += amount_with_tax
            share_per_person = amount_with_tax / len(e['participants'])
            
            for p in e['participants']:
                participant_shares[p] += share_per_person

            expense_data.append({
                '項目': e['item'],
                '金額': e['amount'],
                '是否付稅': '是' if e['is_taxable'] else '否',
                '稅率': f"{e['tax_rate']:.2%}" if e['is_taxable'] else 'N/A',
                '含稅金額': amount_with_tax,
                '參與者': ', '.join(e['participants']),
                **{f'{p} 應付': share_per_person if p in e['participants'] else 0 for p in participant_shares}
            })

        expense_df = pd.DataFrame(expense_data)
        st.subheader('支出摘要')
        st.write(expense_df)
        
        st.subheader('總計')
        st.write(f"總金額（含稅）：{total_amount:.2f}")
        
        # 顯示每人應付金額
        st.subheader('每人應付金額')
        for p in ['Leo', 'Yihua', 'Cyclone', 'Vicky']:
            st.write(f"{p} 總應付：{participant_shares[p]:.2f}")

    else:
        st.write('此帳單暫無支出記錄')

# 主應用邏輯
if st.session_state.page == 'overview':
    show_overview()
elif st.session_state.page in st.session_state.bills:
    show_detail_bill(st.session_state.page)