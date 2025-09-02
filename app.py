from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
import time
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# Firebase konfiguratsiyasi
firebase_config = {
    "apiKey": "AIzaSyDBwAbAmhYZbyNmmq83uf46Qn47TdUveac",
    "authDomain": "finance-control-apps.firebaseapp.com",
    "databaseURL": "https://finance-control-apps-default-rtdb.firebaseio.com",
    "projectId": "finance-control-apps",
    "storageBucket": "finance-control-apps.firebasestorage.app",
    "messagingSenderId": "289705043842",
    "appId": "1:289705043842:web:8c42eff9161fa77251519b",
    "measurementId": "G-31B18G8CFM"
}

# Firebase initialization
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_config['databaseURL']
    })
    print("Firebase admin initialized successfully")
except Exception as e:
    print(f"Firebase admin initialization failed: {e}")

# Ma'lumotlar strukturasi
SK = {
    'CATS': 'mf_categories',
    'TXS': 'mf_transactions',
    'THEME': 'mf_theme',
    'LANG': 'mf_language',
    'USERS': 'mf_users',
    'CURRENT_USER': 'mf_current_user',
    'PASSWORD_RESET_CODES': 'mf_password_reset_codes',
    'PHONE_TO_USERNAMES': 'mf_phone_to_usernames'
}

# Yordamchi funksiyalar
def get_db_ref(path):
    return db.reference(path)

def validate_phone(phone):
    return phone.startswith('+998') and len(phone) == 13

# API endpoints
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Login va parol kiritishingiz kerak',
                'show_for': 3
            }), 400
        
        users_ref = get_db_ref(SK['USERS'])
        user_data = users_ref.child(username).get()
        
        if not user_data or user_data.get('password') != password:
            return jsonify({
                'success': False,
                'message': 'Noto‘g‘ri login yoki parol',
                'show_for': 3
            }), 401
        
        # Joriy foydalanuvchini saqlash
        current_user_ref = get_db_ref(SK['CURRENT_USER'])
        current_user_ref.set(user_data)
        
        return jsonify({
            'success': True,
            'user': user_data,
            'message': 'Muvaffaqiyatli kirish'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}',
            'show_for': 3
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name', '').strip()
        username = data.get('username', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        # Validatsiya
        if not all([name, username, phone, password, confirm_password]):
            return jsonify({
                'success': False,
                'message': 'Barcha maydonlarni to\'ldirishingiz kerak',
                'show_for': 3
            }), 400
        
        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Parollar mos kelmadi',
                'show_for': 3
            }), 400
        
        if not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': 'Telefon raqam formati noto‘g‘ri. +998901234567 formatida kiriting',
                'show_for': 3
            }), 400
        
        # Login bandligini tekshirish
        users_ref = get_db_ref(SK['USERS'])
        if users_ref.child(username).get():
            return jsonify({
                'success': False,
                'message': 'Bu login allaqachon mavjud',
                'show_for': 3
            }), 400
        
        # Telefon raqamiga bog'langan loginlar
        phone_ref = get_db_ref(f"{SK['PHONE_TO_USERNAMES']}/{phone.replace('+', '_plus_')}")
        phone_usernames = phone_ref.get() or []
        
        # 3 tadan ortiq loginlarni tekshirish
        if len(phone_usernames) >= 3:
            return jsonify({
                'success': False,
                'message': 'Bu telefon raqamiga bog\'langan hisoblar soni chegaradan oshdi (maksimum 3)',
                'show_for': 3
            }), 400
        
        # Yangi foydalanuvchini yaratish
        user_data = {
            'name': name,
            'username': username,
            'phone': phone,
            'password': password,
            'registered': time.time(),
            'avatar': None
        }
        
        users_ref.child(username).set(user_data)
        
        # Telefon raqamiga login qo'shish
        if username not in phone_usernames:
            phone_usernames.append(username)
            phone_ref.set(phone_usernames)
        
        # Foydalanuvchi uchun boshlang'ich kategoriyalar
        categories_ref = get_db_ref(f"{SK['CATS']}/{username}")
        default_categories = ['Oziq-ovqat', 'Transport', 'Kiyim', 'Kommunal', 'Maishiy', 'Salomatlik', 'Ta\'lim', 'Koʻngilochar']
        categories_ref.set(default_categories)
        
        # Tranzaksiyalar
        transactions_ref = get_db_ref(f"{SK['TXS']}/{username}")
        transactions_ref.set([])
        
        return jsonify({
            'success': True,
            'message': 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}',
            'show_for': 3
        }), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'success': False, 'message': 'Username required'}), 400
        
        ref = get_db_ref(f"{SK['TXS']}/{username}")
        transactions = ref.get() or []
        
        return jsonify({
            'success': True,
            'transactions': transactions
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        }), 500

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'Username required'}), 400
        
        transaction = {
            'id': str(int(time.time() * 1000)),  # Unique ID
            'type': data.get('type'),
            'amount': float(data.get('amount', 0)),
            'category': data.get('category'),
            'note': data.get('note', ''),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d'))
        }
        
        ref = get_db_ref(f"{SK['TXS']}/{username}")
        transactions = ref.get() or []
        transactions.append(transaction)
        ref.set(transactions)
        
        return jsonify({
            'success': True,
            'message': 'Tranzaksiya qo\'shildi'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        }), 500

@app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'success': False, 'message': 'Username required'}), 400
        
        ref = get_db_ref(f"{SK['TXS']}/{username}")
        transactions = ref.get() or []
        
        # Tranzaksiyani topish va o'chirish
        updated_transactions = [t for t in transactions if t.get('id') != transaction_id]
        
        if len(updated_transactions) == len(transactions):
            return jsonify({
                'success': False,
                'message': 'Tranzaksiya topilmadi'
            }), 404
        
        ref.set(updated_transactions)
        
        return jsonify({
            'success': True,
            'message': 'Tranzaksiya o\'chirildi'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'success': False, 'message': 'Username required'}), 400
        
        ref = get_db_ref(f"{SK['CATS']}/{username}")
        categories = ref.get() or []
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        }), 500

@app.route('/api/categories', methods=['POST'])
def add_category():
    try:
        data = request.json
        username = data.get('username')
        category_name = data.get('name', '').strip()
        
        if not username or not category_name:
            return jsonify({'success': False, 'message': 'Username va kategoriya nomi kerak'}), 400
        
        ref = get_db_ref(f"{SK['CATS']}/{username}")
        categories = ref.get() or []
        
        if category_name in categories:
            return jsonify({
                'success': False,
                'message': 'Bunday kategoriya mavjud'
            }), 400
        
        categories.append(category_name)
        ref.set(categories)
        
        return jsonify({
            'success': True,
            'message': 'Kategoriya qo\'shildi'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        }), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.json
        phone = data.get('phone', '').strip()
        
        if not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': 'Telefon raqam formati noto‘g‘ri',
                'show_for': 3
            }), 400
        
        # Telefon raqamiga mos foydalanuvchilarni topish
        phone_key = phone.replace('+', '_plus_')
        phone_ref = get_db_ref(f"{SK['PHONE_TO_USERNAMES']}/{phone_key}")
        usernames = phone_ref.get() or []
        
        if not usernames:
            return jsonify({
                'success': False,
                'message': 'Telefon raqamiga mos foydalanuvchi topilmadi',
                'show_for': 3
            }), 404
        
        # Tasdiqlash kodi yaratish
        code = str(random.randint(10000, 99999))
        
        # Kodni saqlash
        reset_ref = get_db_ref(f"{SK['PASSWORD_RESET_CODES']}/{phone_key}")
        reset_ref.set({
            'code': code,
            'expires': time.time() + 600,  # 10 daqiqa
            'usernames': usernames
        })
        
        # Kodni yuborish (simulyatsiya)
        print(f"Tasdiqlash kodi {phone} raqamiga yuborildi: {code}")
        
        return jsonify({
            'success': True,
            'message': 'Tasdiqlash kodi yuborildi',
            'usernames': usernames
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}',
            'show_for': 3
        }), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        phone = data.get('phone', '').strip()
        username = data.get('username', '').strip()
        code = data.get('code', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not all([phone, username, code, new_password]):
            return jsonify({
                'success': False,
                'message': 'Barcha maydonlarni to\'ldirishingiz kerak',
                'show_for': 3
            }), 400
        
        # Tasdiqlash kodini tekshirish
        phone_key = phone.replace('+', '_plus_')
        reset_ref = get_db_ref(f"{SK['PASSWORD_RESET_CODES']}/{phone_key}")
        reset_data = reset_ref.get()
        
        if not reset_data or reset_data.get('code') != code or reset_data.get('expires', 0) < time.time():
            return jsonify({
                'success': False,
                'message': 'Noto\'g\'ri yoki muddati o\'tgan tasdiqlash kodi',
                'show_for': 3
            }), 400
        
        # Foydalanuvchi mavjudligini tekshirish
        users_ref = get_db_ref(SK['USERS'])
        user_data = users_ref.child(username).get()
        
        if not user_data:
            return jsonify({
                'success': False,
                'message': 'Foydalanuvchi topilmadi',
                'show_for': 3
            }), 404
        
        # Parolni yangilash
        user_data['password'] = new_password
        users_ref.child(username).set(user_data)
        
        # Tasdiqlash kodini o'chirish
        reset_ref.delete()
        
        return jsonify({
            'success': True,
            'message': 'Parol muvaffaqiyatli o\'zgartirildi!'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}',
            'show_for': 3
        }), 500

@app.route('/api/profile', methods=['POST'])
def update_profile():
    try:
        data = request.json
        username = data.get('username')
        name = data.get('name', '').strip()
        new_username = data.get('new_username', '').strip()
        avatar = data.get('avatar')
        
        if not username:
            return jsonify({'success': False, 'message': 'Username required'}), 400
        
        users_ref = get_db_ref(SK['USERS'])
        user_data = users_ref.child(username).get()
        
        if not user_data:
            return jsonify({
                'success': False,
                'message': 'Foydalanuvchi topilmadi'
            }), 404
        
        # Yangi login bandligini tekshirish
        if new_username and new_username != username:
            if users_ref.child(new_username).get():
                return jsonify({
                    'success': False,
                    'message': 'Yangi login allaqachon band qilingan'
                }), 400
            
            # Ma'lumotlarni yangi login ostiga ko'chirish
            user_data['username'] = new_username
            user_data['name'] = name
            
            if avatar:
                user_data['avatar'] = avatar
            
            # Yangi foydalanuvchini yaratish
            users_ref.child(new_username).set(user_data)
            
            # Eski foydalanuvchini o'chirish
            users_ref.child(username).delete()
            
            # Kategoriyalarni ko'chirish
            cats_ref = get_db_ref(f"{SK['CATS']}/{username}")
            categories = cats_ref.get() or []
            get_db_ref(f"{SK['CATS']}/{new_username}").set(categories)
            cats_ref.delete()
            
            # Tranzaksiyalarni ko'chirish
            txs_ref = get_db_ref(f"{SK['TXS']}/{username}")
            transactions = txs_ref.get() or []
            get_db_ref(f"{SK['TXS']}/{new_username}").set(transactions)
            txs_ref.delete()
            
            # Telefon raqamidagi eski loginni yangilash
            phone_key = user_data['phone'].replace('+', '_plus_')
            phone_ref = get_db_ref(f"{SK['PHONE_TO_USERNAMES']}/{phone_key}")
            phone_usernames = phone_ref.get() or []
            
            if username in phone_usernames:
                phone_usernames.remove(username)
                phone_usernames.append(new_username)
                phone_ref.set(phone_usernames)
            
            username = new_username
        else:
            # Faqat ma'lumotlarni yangilash
            user_data['name'] = name
            if avatar:
                user_data['avatar'] = avatar
            users_ref.child(username).set(user_data)
        
        return jsonify({
            'success': True,
            'message': 'Profil yangilandi',
            'user': user_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)