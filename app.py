import streamlit as st
import sqlite3
import pandas as pd
import os
import uuid
import datetime

st.set_page_config(page_title="Volunteer Management System", page_icon="🤝", layout="wide")

def init_db():
    conn = sqlite3.connect("volunteer.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            location TEXT,
            skills_required TEXT,
            number_volunteers_needed INTEGER DEFAULT 3,
            status TEXT DEFAULT 'open',
            urgency TEXT,
            date_needed TEXT,
            created_date TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volunteer_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            availability TEXT,
            status TEXT DEFAULT 'available',
            created_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect("volunteer.db", check_same_thread=False)

def sync_csv_data():
    csv_path = "data.csv"
    
    if not os.path.exists(csv_path):
        sample_data = {
            'request_id': [101, 102, 103, 104, 105],
            'need_type': ['Food', 'Medical', 'Admin', 'Teaching', 'Logistics'],
            'description': ['Food distribution', 'Medical camp', 'Registration desk', 'Online classes', 'Material transport'],
            'location': ['Meerut', 'Delhi', 'Noida', 'Gurgaon', 'Meerut'],
            'urgency': ['High', 'Medium', 'Low', 'High', 'Medium']
        }
        pd.DataFrame(sample_data).to_csv(csv_path, index=False)
        st.success("✅ Sample data.csv created!")

    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    
    data_list = []
    for i, row in df.iterrows():
        record = {
            'request_id': f"REQ_{i+1:03d}",
            'title': str(row.get('need_type', f'Request {i+1}')),
            'description': str(row.get('description', 'No description')),
            'location': str(row.get('location', 'Meerut')),
            'skills_required': str(row.get('need_type', 'General')),
            'number_volunteers_needed': 3,
            'status': 'open',
            'urgency': str(row.get('urgency', 'Medium')),
            'date_needed': '2026-12-31',
            'created_date': datetime.datetime.now().isoformat()
        }
        data_list.append(record)

    conn = get_db_connection()
    df_db = pd.DataFrame(data_list)
    df_db.to_sql('Requests', conn, if_exists='replace', index=False)
    conn.close()
    
    st.success(f"🎉 {len(df_db)} records synced!")
    st.balloons()
    st.rerun()

def volunteer_form():
    with st.sidebar.form("vol_form"):
        st.header("👤 Register")
        vol_id = str(uuid.uuid4())[:8]
        st.markdown(f"*ID:* `{vol_id}`")
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        skills = st.multiselect("Skills", ["Food", "Medical", "Admin", "Logistics", "Teaching"])
        
        if st.form_submit_button("✅ Register"):
            if name and email:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Volunteers (volunteer_id, name, email, phone, skills, availability, created_date) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (vol_id, name, email, phone, ",".join(skills), "Any", datetime.datetime.now().isoformat()))
                conn.commit()
                conn.close()
                st.sidebar.success(f"✅ {name} registered!")
                st.rerun()
            else:
                st.sidebar.error("❌ Name & Email required!")

def get_stats():
    conn = get_db_connection()
    stats = {}
    try:
        stats['open_req'] = pd.read_sql_query("SELECT COUNT(*) FROM Requests WHERE status='open'", conn).iloc[0, 0]
        stats['total_vol'] = pd.read_sql_query("SELECT COUNT(*) FROM Volunteers", conn).iloc[0, 0]
        stats['total_req'] = pd.read_sql_query("SELECT COUNT(*) FROM Requests", conn).iloc[0, 0]
    except:
        stats = {'open_req': 0, 'total_vol': 0, 'total_req': 0}
    conn.close()
    return stats

def dashboard():
    stats = get_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("📋 Open Requests", stats['open_req'])
    c2.metric("👥 Volunteers", stats['total_vol'])
    c3.metric("📈 Total Requests", stats['total_req'])

def main():
    init_db()
    st.title("🤝 Volunteer Management System")
    
    st.sidebar.header("⚙️ Controls")
    if st.sidebar.button("🚀 SYNC DATA", use_container_width=True, type="primary"):
        sync_csv_data()
    
    volunteer_form()
    
    t1, t2, t3 = st.tabs(["📊 Dashboard", "📋 Requests", "👥 Volunteers"])
    
    with t1:
        dashboard()
        
    with t2: 
        conn = get_db_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM Requests ORDER BY id DESC", conn)
            st.dataframe(df, use_container_width=True)
        except:
            st.info("No requests. Click SYNC!")
        conn.close()
        
    with t3:
        conn = get_db_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM Volunteers ORDER BY id DESC", conn)
            st.dataframe(df, use_container_width=True)
        except:
            st.info("No volunteers yet.")
        conn.close()

if __name__ == "__main__":
    main()