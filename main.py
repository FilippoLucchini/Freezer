# requirements.txt
# streamlit
# qrcode
# sqlite3 (già incluso in Python)

# main.py
import streamlit as st
import sqlite3
import qrcode
from io import BytesIO
from PIL import Image

def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Esempio semplice: username e password hardcoded
    users = {
        "ddlab": "ddlabno1"
    }

    if st.button("Accedi"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Username o password errati")
    return False
    
# --- DATABASE SETUP ---
conn = sqlite3.connect("freezer_db.sqlite")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS freezer (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    descrizione TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS cassetto (
    id INTEGER PRIMARY KEY,
    freezer_id INTEGER,
    nome TEXT,
    FOREIGN KEY (freezer_id) REFERENCES freezer(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS box (
    id INTEGER PRIMARY KEY,
    cassetto_id INTEGER,
    posizione TEXT,
    progetto TEXT,
    tipo_campione TEXT,
    FOREIGN KEY (cassetto_id) REFERENCES cassetto(id)
)''')

conn.commit()

# --- FUNCTIONS ---
def get_freezers():
    return c.execute("SELECT * FROM freezer").fetchall()

def get_cassetti(freezer_id):
    return c.execute("SELECT * FROM cassetto WHERE freezer_id = ?", (freezer_id,)).fetchall()

def get_box(cassetto_id):
    return c.execute("SELECT * FROM box WHERE cassetto_id = ?", (cassetto_id,)).fetchall()

def generate_qr_code(link):
    qr = qrcode.make(link)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return Image.open(buf)

# --- STREAMLIT UI ---
if not login():
    st.stop()
    
st.set_page_config(layout="wide")
st.title("DDLAB Freezer Manager")

query_params = st.query_params
freezer_id_from_url = query_params.get("freezer_id", None)

freezers = get_freezers()

if freezer_id_from_url:
    try:
        freezer_id = int(freezer_id_from_url)
        freezer_data = next((f for f in freezers if f[0] == freezer_id), None)
        page = freezer_data[1] if freezer_data else "Home"
    except ValueError:
        freezer_id = None
        page = "Home"
else:
    page = st.sidebar.selectbox("Navigazione", ["Home"] + [f[1] for f in freezers])

if page == "Home":
    st.header("Freezer disponibili")
    for f in get_freezers():
        st.subheader(f"{f[1]}")
        st.write(f"Descrizione: {f[2]}")

    with st.expander("Aggiungi nuovo freezer"):
        nome = st.text_input("Nome freezer")
        descrizione = st.text_input("Descrizione")
        if st.button("Aggiungi"):
            c.execute("INSERT INTO freezer (nome, descrizione) VALUES (?, ?)", (nome, descrizione))
            conn.commit()
            st.success("Freezer aggiunto")

else:
    freezer_data = next((f for f in freezers if f[1] == page), None)
    if freezer_data:
        freezer_id = freezer_data[0]
        st.header(f"{freezer_data[1]} - Torri/Cassetti")

        for cass in get_cassetti(freezer_id):
            with st.expander(f"Torre/Cassetto {cass[2]}"):
                box_list = get_box(cass[0])
                for b in box_list:
                    cols = st.columns([4, 1])
                    cols[0].write(f"Box {b[2]} | Progetto: {b[3]} | Tipo: {b[4]}")
                    if cols[1].button("Rimuovi", key=f"rm_{b[0]}"):
                        c.execute("DELETE FROM box WHERE id = ?", (b[0],))
                        conn.commit()
                        st.experimental_rerun()

                st.markdown("---")
                with st.form(key=f"add_box_{cass[0]}"):
                    posizione = st.text_input("Posizione (es. A1)", key=f"pos_{cass[0]}")
                    progetto = st.text_input("Progetto", key=f"proj_{cass[0]}")
                    tipo = st.text_input("Tipo campione", key=f"tipo_{cass[0]}")
                    if st.form_submit_button("Aggiungi box"):
                        c.execute("INSERT INTO box (cassetto_id, posizione, progetto, tipo_campione) VALUES (?, ?, ?, ?)",
                                  (cass[0], posizione, progetto, tipo))
                        conn.commit()
                        st.success("Box aggiunto")

        with st.expander("Aggiungi nuovo cassetto"):
            nome_cassetto = st.text_input("Nome cassetto")
            if st.button("Aggiungi cassetto"):
                c.execute("INSERT INTO cassetto (freezer_id, nome) VALUES (?, ?)", (freezer_id, nome_cassetto))
                conn.commit()
                st.success("Cassetto aggiunto")
    else:
        st.error("Freezer non trovato.")
