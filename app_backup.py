import streamlit as st
import sqlite3
import pandas as pd
import os

# Page config
st.set_page_config(
    page_title="Volunteer Management System",
    page_icon="🤝",
    layout="wide"
)

# Database initialization function
@st.cache_resource
def init_db():
    """Initialize the SQLite database with Requests and Volunteers tables"""
    
    db_path = "volunteer.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Requests table
    # Note: Update these columns to match your exact data.csv structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            location TEXT,
            date_needed TEXT,
            time_needed TEXT,
            skills_required TEXT,
            number_volunteers_needed INTEGER,
            status TEXT DEFAULT 'open',
            created_date TEXT,
            deadline TEXT
        )
    """)
    
    # Create Volunteers table
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
            created_date TEXT,
            last_login TEXT
        )
    """)
    
    # Create Requests_Volunteers junction table for many-to-many relationship
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests_Volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            volunteer_id INTEGER,
            assigned_date TEXT,
            status TEXT DEFAULT 'assigned',
            FOREIGN KEY (request_id) REFERENCES Requests (id),
            FOREIGN KEY (volunteer_id) REFERENCES Volunteers (id)
        )
    """)
    
    conn.commit()
    
    # Check if data.csv exists and import it
    if os.path.exists("data.csv"):
        try:
            df = pd.read_csv("data.csv")
            # Insert data into Requests table (adjust column mapping as needed)
            df.to_sql('Requests', conn, if_exists='append', index=False)
            st.success(f"Imported {len(df)} requests from data.csv")
        except Exception as e:
            st.warning(f"Could not import data.csv: {str(e)}")
    
    conn.close()
    return db_path

# Database connection function
@st.cache_resource
def get_db_connection():
    """Get a database connection"""
    init_db()  # Ensure DB is initialized
    conn = sqlite3.connect("volunteer.db", check_same_thread=False)
    return conn

# Initialize the app
def main():
    st.title("🤝 Volunteer Management System")
    st.markdown("---")
    
    # Initialize database on first run
    if "db_initialized" not in st.session_state:
        with st.spinner("Initializing database..."):
            db_path = init_db()
            st.session_state.db_initialized = True
            st.success("✅ Database initialized successfully!")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "Requests", "Volunteers", "Assignments"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Requests":
        show_requests()
    elif page == "Volunteers":
        show_volunteers()
    elif page == "Assignments":
        show_assignments()

def show_dashboard():
    """Dashboard page"""
    st.header("📊 Dashboard")
    
    conn = get_db_connection()
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    
    open_requests = pd.read_sql_query("SELECT COUNT(*) as count FROM Requests WHERE status = 'open'", conn).iloc[0]['count']
    total_volunteers = pd.read_sql_query("SELECT COUNT(*) as count FROM Volunteers", conn).iloc[0]['count']
    total_requests = pd.read_sql_query("SELECT COUNT(*) as count FROM Requests", conn).iloc[0]['count']
    assignments = pd.read_sql_query("SELECT COUNT(*) as count FROM Requests_Volunteers", conn).iloc[0]['count']
    
    with col1:
        st.metric("Open Requests", open_requests)
    with col2:
        st.metric("Total Volunteers", total_volunteers)
    with col3:
        st.metric("Total Requests", total_requests)
    with col4:
        st.metric("Assignments", assignments)
    
    conn.close()

def show_requests():
    """Requests management page"""
    st.header("📋 Volunteer Requests")
    
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM Requests", conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)

def show_volunteers():
    """Volunteers management page"""
    st.header("👥 Volunteers")
    
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM Volunteers", conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)

def show_assignments():
    """Assignments management page"""
    st.header("🔗 Assignments")
    
    conn = get_db_connection()
    query = """
    SELECT r.title, v.name, rv.status, rv.assigned_date
    FROM Requests_Volunteers rv
    JOIN Requests r ON rv.request_id = r.id
    JOIN Volunteers v ON rv.volunteer_id = v.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
    
    import streamlit as st
import sqlite3
import pandas as pd
import os

# ... (keep all previous imports and functions from the original app.py)

# Add this new function for CSV upload and import
def upload_and_import_csv():
    """Handle CSV file upload and import to Requests table"""
    st.header("📤 Upload Requests CSV")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload your requests data.csv file"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Display preview
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
            
            with col2:
                st.metric("Rows", len(df))
                st.metric("Columns", len(df.columns))
                st.text(f"Size: {uploaded_file.size / 1024:.1f} KB")
            
            # Show columns
            st.subheader("📊 Columns Detected")
            st.write(df.columns.tolist())
            
            # Import button
            if st.button("💾 Import to Database", type="primary"):
                conn = get_db_connection()
                
                try:
                    # Clear existing data (optional - uncomment if needed)
                    # cursor = conn.cursor()
                    # cursor.execute("DELETE FROM Requests")
                    # conn.commit()
                    
                    # Import to database
                    success = df.to_sql(
                        'Requests', 
                        conn, 
                        if_exists='append',  # 'replace' to overwrite, 'append' to add
                        index=False
                    )
                    
                    conn.close()
                    
                    if success:
                        st.success(f"✅ Successfully imported {len(df)} requests!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Import failed!")
                        
                except Exception as e:
                    st.error(f"❌ Error importing data: {str(e)}")
                    st.exception(e)
    
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.exception(e)

def show_pending_requests():
    """Display current pending requests"""
    st.header("⏳ Pending Requests")
    
    conn = get_db_connection()
    
    # Query for pending/open requests
    query = """
    SELECT 
        id,
        request_id,
        title,
        description,
        location,
        date_needed,
        time_needed,
        skills_required,
        number_volunteers_needed,
        status,
        created_date,
        deadline
    FROM Requests 
    WHERE status IN ('open', 'pending')
    ORDER BY date_needed ASC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        st.info("🎉 No pending requests! All requests are fulfilled.")
    else:
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pending Requests", len(df))
        with col2:
            total_needed = df['number_volunteers_needed'].sum()
            st.metric("Volunteers Needed", total_needed)
        with col3:
            urgent = len(df[df['date_needed'] < pd.Timestamp.now().strftime('%Y-%m-%d')])
            st.metric("Urgent", urgent)
        
        # Dataframe with enhanced styling
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["open", "pending", "assigned", "fulfilled", "cancelled"],
                    required=True
                ),
                "number_volunteers_needed": st.column_config.NumberColumn(
                    "Volunteers Needed",
                    format="%d"
                ),
                "date_needed": st.column_config.DateColumn("Date Needed")
            },
            hide_index=True
        )

# Updated main function with new pages
def main():
    st.title("🤝 Volunteer Management System")
    st.markdown("---")
    
    # Initialize database
    if "db_initialized" not in st.session_state:
        with st.spinner("Initializing database..."):
            init_db()
            st.session_state.db_initialized = True
            st.success("✅ Database ready!")
    
    # Enhanced sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "📤 Upload CSV", "⏳ Pending Requests", "📋 All Requests", "👥 Volunteers", "🔗 Assignments"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "📤 Upload CSV":
        upload_and_import_csv()
    elif page == "⏳ Pending Requests":
        show_pending_requests()
    elif page == "📋 All Requests":
        show_requests()
    elif page == "👥 Volunteers":
        show_volunteers()
    elif page == "🔗 Assignments":
        show_assignments()
        import streamlit as st
import sqlite3
import pandas as pd
import uuid
import datetime
        
 

# ... (keep all previous imports and functions)

# Add this new function for volunteer registration
def volunteer_registration_form():
    """Sidebar form for volunteer registration"""
    st.sidebar.header("👤 Volunteer Registration")
    
    # Form container
    with st.sidebar.form("volunteer_form", clear_on_submit=True):
        # Generate unique volunteer ID
        volunteer_id = st.text_input("Volunteer ID", value=str(uuid.uuid4())[:8], disabled=True)
        
        name = st.text_input("Full Name", placeholder="Enter your full name")
        email = st.text_input("Email", placeholder="your.email@example.com")
        phone = st.text_input("Phone", placeholder="(123) 456-7890")
        
        # Skills multi-select
        skills = st.multiselect(
            "Skills (select all that apply)",
            ["Food Service", "Medical/First Aid", "Childcare", "Elderly Care", 
             "Construction", "Cleanup", "Translation", "Administrative", 
             "Driving", "Tech Support", "Teaching", "Other"],
            max_selections=5
        )
        
        # Location multi-select (common locations - customize as needed)
        preferred_locations = st.multiselect(
            "Preferred Locations",
            ["Downtown", "East Side", "West Side", "North Side", "South Side", 
             "Suburbs", "Rural", "Any Location"],
            default=["Any Location"]
        )
        
        # Availability
        availability = st.multiselect(
            "Availability",
            ["Weekdays", "Weekends", "Mornings", "Afternoons", "Evenings", 
             "Anytime", "Emergencies Only"],
            default=["Anytime"]
        )
        
        # Submit button
        submitted = st.form_submit_button("✅ Register as Volunteer", use_container_width=True)
        
        if submitted:
            # Validation
            if not name.strip():
                st.sidebar.error("❌ Please enter your name")
                return
            
            if not email or "@" not in email:
                st.sidebar.error("❌ Please enter a valid email")
                return
            
            try:
                # Prepare data
                skills_str = ", ".join(skills) if skills else "None"
                locations_str = ", ".join(preferred_locations)
                availability_str = ", ".join(availability)
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Insert volunteer
                cursor.execute("""
                    INSERT INTO Volunteers 
                    (volunteer_id, name, email, phone, skills, availability, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    volunteer_id,
                    name.strip(),
                    email.strip(),
                    phone.strip(),
                    skills_str,
                    availability_str,
                    datetime.datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                
                # Success message
                st.sidebar.success(f"🎉 Welcome {name}! Your Volunteer ID is: **{volunteer_id}**")
                st.sidebar.balloons()
                st.sidebar.markdown("---")
                st.sidebar.info("💡 Save your Volunteer ID for future reference")
                
                # Show registration summary
                with st.sidebar.expander("📋 Registration Summary"):
                    st.success("**Details:**")
                    st.write(f"**ID:** {volunteer_id}")
                    st.write(f"**Name:** {name}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Skills:** {skills_str}")
                    st.write(f"**Locations:** {locations_str}")
                    st.write(f"**Availability:** {availability_str}")
                
                st.rerun()
                
            except sqlite3.IntegrityError:
                st.sidebar.error("❌ Volunteer ID already exists. Please refresh the page.")
            except Exception as e:
                st.sidebar.error(f"❌ Registration failed: {str(e)}")
                st.sidebar.exception(e)

# Updated main function
def main():
    st.title("🤝 Volunteer Management System")
    st.markdown("---")
    
    # Initialize database
    if "db_initialized" not in st.session_state:
        with st.spinner("Initializing database..."):
            init_db()
            st.session_state.db_initialized = True
    
    # VOLUNTEER REGISTRATION SIDEBAR FORM (always visible)
    volunteer_registration_form()
    
    # Main navigation (below the registration form)
    st.sidebar.markdown("---")
    st.sidebar.title("📋 Navigation")
    if st.sidebar.button("🚀 Force Sync CSV Data"):
        import sqlite3
        import pandas as pd
        import os
    
        csv_path = os.path.join(os.path.dirname(__file__), "data.csv")
    
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df.columns = [c.strip() for c in df.columns]
                conn = sqlite3.connect("volunteer.db")
                df.to_sql("Requests", conn, if_exists="replace", index=False)
                conn.close()
                st.sidebar.success("Mubarak ho! Data load ho gaya.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
        else:
            st.sidebar.error("Lafda ho gaya! data.csv file nahi mili.")
   
    
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "📤 Upload CSV", "⏳ Pending Requests", 
         "📋 All Requests", "👥 Volunteers", "🔗 Assignments"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "📤 Upload CSV":
        upload_and_import_csv()
    elif page == "⏳ Pending Requests":
        show_pending_requests()
    elif page == "📋 All Requests":
        show_requests()
    elif page == "👥 Volunteers":
        show_volunteers()
    elif page == "🔗 Assignments":
        show_assignments()

# Update the Volunteers table creation in init_db() to ensure all columns exist
def init_db():
    """Updated init_db with complete Volunteers table"""
    db_path = "volunteer.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Requests table (same as before)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            location TEXT,
            date_needed TEXT,
            time_needed TEXT,
            skills_required TEXT,
            number_volunteers_needed INTEGER,
            status TEXT DEFAULT 'open',
            created_date TEXT,
            deadline TEXT
        )
    """)
    
    # Updated Volunteers table with all required columns
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
            created_date TEXT,
            last_login TEXT
        )
    """)
    
    # Junction table (same as before)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Requests_Volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            volunteer_id INTEGER,
            assigned_date TEXT,
            status TEXT DEFAULT 'assigned',
            FOREIGN KEY (request_id) REFERENCES Requests (id),
            FOREIGN KEY (volunteer_id) REFERENCES Volunteers (id)
        )
    """)
    
    conn.commit()
    conn.close()
    return db_path

import streamlit as st
import sqlite3
import pandas as pd
import re
from difflib import SequenceMatcher

# Add these new functions to your app.py

def smart_match_volunteers(request_row):
    """Find volunteers matching a specific request using skills and location"""
    request_id = request_row['id']
    skills_needed = request_row.get('skills_required', '').lower()
    location_needed = request_row.get('location', '').lower()
    
    conn = get_db_connection()
    
    # Query volunteers
    query = """
    SELECT 
        v.id,
        v.volunteer_id,
        v.name,
        v.email,
        v.phone,
        v.skills,
        v.availability,
        v.status,
        v.created_date
    FROM Volunteers v
    WHERE v.status = 'available'
    """
    
    df_volunteers = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_volunteers.empty:
        return pd.DataFrame()
    
    # Smart matching logic
    matches = []
    
    for _, vol in df_volunteers.iterrows():
        score = 0
        reasons = []
        
        # Skill matching (fuzzy matching)
        vol_skills = vol['skills'].lower() if pd.notna(vol['skills']) else ""
        skill_keywords = extract_keywords(skills_needed)
        
        skill_matches = 0
        for keyword in skill_keywords:
            if keyword in vol_skills:
                skill_matches += 1
                reasons.append(f"✅ {keyword}")
        
        skill_score = min(skill_matches / max(len(skill_keywords), 1) * 50, 50)
        score += skill_score
        
        # Location matching
        if pd.notna(location_needed) and location_needed:
            vol_has_location = False
            location_keywords = extract_keywords(location_needed)
            
            for loc_keyword in location_keywords:
                if loc_keyword.lower() in vol['availability'].lower():
                    vol_has_location = True
                    break
            
            if vol_has_location or "any location" in vol['availability'].lower():
                score += 30
                reasons.append("📍 Location match")
            else:
                reasons.append("📍 Location preference")
        
        # Availability bonus (if request has time info)
        if 'time_needed' in request_row and pd.notna(request_row['time_needed']):
            if any(time in vol['availability'].lower() for time in ['anytime', 'weekdays', 'weekends']):
                score += 20
                reasons.append("⏰ Available")
        
        # Name the match
        match_data = {
            'volunteer_id': vol['volunteer_id'],
            'name': vol['name'],
            'email': vol['email'],
            'phone': vol['phone'],
            'skills': vol['skills'],
            'availability': vol['availability'],
            'match_score': round(score, 1),
            'skill_score': round(skill_score, 1),
            'reasons': " | ".join(reasons[:3]),  # Top 3 reasons
            'volunteer_db_id': vol['id']
        }
        
        matches.append(match_data)
    
    # Convert to DataFrame and sort by score
    matches_df = pd.DataFrame(matches)
    if not matches_df.empty:
        matches_df = matches_df.sort_values('match_score', ascending=False).head(10)
    
    return matches_df

def extract_keywords(text):
    """Extract key skill/location keywords from text"""
    if pd.isna(text) or not text:
        return []
    
    # Common skill patterns
    patterns = [
        r'\bfood\b', r'\bmedical\b', r'\bfirst aid\b', r'\bchildcare?\b', 
        r'\belderly\b', r'\bconstruction\b', r'\bcleanup\b', r'\btranslation\b',
        r'\badmin\b', r'\bdriving\b', r'\btech\b', r'\bteaching\b'
    ]
    
    keywords = re.findall(r'\b\w+\b', text.lower())
    return list(set(keywords))  # Remove duplicates

# Updated show_pending_requests function with Smart Match
def show_pending_requests():
    """Display pending requests with Smart Match button"""
    st.header("⏳ Pending Requests")
    
    conn = get_db_connection()
    query = """
    SELECT * FROM Requests 
    WHERE status IN ('open', 'pending')
    ORDER BY date_needed ASC
    """
    df_requests = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_requests.empty:
        st.info("🎉 No pending requests!")
        return
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Requests", len(df_requests))
    with col2:
        total_needed = df_requests['number_volunteers_needed'].sum()
        st.metric("Volunteers Needed", total_needed)
    with col3:
        urgent = len(df_requests[df_requests['date_needed'] < pd.Timestamp.now().strftime('%Y-%m-%d')])
        st.metric("Urgent", urgent)
    
    # Requests table with Smart Match
    for idx, request in df_requests.iterrows():
        with st.expander(f"📋 {request['title']} - {request['location']} ({request['number_volunteers_needed']} needed)"):
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {request.get('description', 'N/A')}")
                st.markdown(f"**Date:** {request.get('date_needed', 'N/A')}")
                st.markdown(f"**Time:** {request.get('time_needed', 'N/A')}")
                st.markdown(f"**Skills:** {request.get('skills_required', 'Any')}")
            
            with col2:
                if st.button(f"🤖 Find Volunteers", key=f"match_{request['id']}", use_container_width=True):
                    with st.spinner("🔍 Finding best matches..."):
                        matches_df = smart_match_volunteers(request)
                        
                        if matches_df.empty:
                            st.warning("😔 No volunteers found. Try registering more volunteers!")
                        else:
                            # Display matches table
                            st.success(f"🎯 Found {len(matches_df)} matching volunteers!")
                            
                            st.dataframe(
                                matches_df,
                                use_container_width=True,
                                column_config={
                                    "match_score": st.column_config.ProgressColumn(
                                        "Match Score",
                                        format="%.1f%%",
                                        min_value=0,
                                        max_value=100
                                    ),
                                    "reasons": st.column_config.TextColumn("Why they match")
                                },
                                hide_index=True
                            )
                            
                            # Action buttons
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button(f"✉️ Email Top 3", key=f"email_{request['id']}"):
                                    top3 = matches_df.head(3)['email'].tolist()
                                    st.code("\n".join(top3))
                                    st.info("📧 Copy these emails to send invitations!")
                            
                            with col_btn2:
                                if st.button(f"💾 Assign Top Match", key=f"assign_{request['id']}"):
                                    top_vol = matches_df.iloc[0]
                                    st.success(f"✅ Assigned {top_vol['name']} to this request!")
                                    # TODO: Add actual assignment logic here
    
    # Summary stats
    st.markdown("---")
    st.subheader("📊 Smart Match Summary")
    conn = get_db_connection()
    volunteer_count = pd.read_sql_query("SELECT COUNT(*) as count FROM Volunteers WHERE status='available'", conn).iloc[0]['count']
    conn.close()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Available Volunteers", volunteer_count)
    with col2:
        st.metric("Pending Requests", len(df_requests))

# Optional: Add to your main navigation
def main():
    # ... existing code ...
    
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "📤 Upload CSV", "⏳ Pending Requests", 
         "📋 All Requests", "👥 Volunteers", "🔗 Assignments", "🤖 Smart Match"]
    )
    if page == "🤖 Smart Match":
        st.header("🤖 Smart Volunteer Matching")
        show_pending_requests()  # Reuse the enhanced function
   







