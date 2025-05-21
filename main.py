
import streamlit as st
import sqlite3
import qrcode
from io import BytesIO
from PIL import Image

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
    numero INTEGER,
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
st.set_page_config(layout="wide")
st.title("Gestione Freezer di Laboratorio")

page = st.sidebar.selectbox("Navigazione", ["Home"] + [f"Freezer {f[0]}" for f in get_freezers()])

if page == "Home":
    st.header("Freezer disponibili")
    for f in get_freezers():
        st.subheader(f"{f[1]}")
        st.write(f"Descrizione: {f[2]}")
        qr_img = generate_qr_code(f"https://freezer-app.streamlit.app/?freezer_id={f[0]}")
        st.image(qr_img, caption="QR Code per accesso diretto", width=150)

    with st.expander("Aggiungi nuovo freezer"):
        nome = st.text_input("Nome freezer")
        descrizione = st.text_input("Descrizione")
        if st.button("Aggiungi"):
            c.execute("INSERT INTO freezer (nome, descrizione) VALUES (?, ?)", (nome, descrizione))
            conn.commit()
            st.success("Freezer aggiunto")

elif "Freezer" in page:
    freezer_id = int(page.split()[-1])
    freezer_data = c.execute("SELECT * FROM freezer WHERE id = ?", (freezer_id,)).fetchone()
    st.header(f"{freezer_data[1]} - Cassetti")

    for cass in get_cassetti(freezer_id):
        with st.expander(f"Cassetto {cass[2]}"):
            box_list = get_box(cass[0])
            for b in box_list:
                cols = st.columns([4, 1])
                cols[0].write(f"Box {b[2]} | Progetto: {b[3]} | Tipo: {b[4]}")
                if cols[1].button("Rimuovi", key=f"rm_{b[0]}"):
                    c.execute("DELETE FROM box WHERE id = ?", (b[0],))
                    conn.commit()
                    st.rerun()

            st.markdown("---")
            with st.form(key=f"add_box_{cass[0]}"):
                posizione = st.text_input("Posizione (es. A1)", key=f"pos_{cass[0]}")
                progetto = st.text_input("Progetto", key=f"proj_{cass[0]}")
                tipo = st.selectbox("Tipo campione", ["WGS", "WES", "RNA", "ALTRO"], key=f"tipo_{cass[0]}")
                if st.form_submit_button("Aggiungi box"):
                    c.execute("INSERT INTO box (cassetto_id, posizione, progetto, tipo_campione) VALUES (?, ?, ?, ?)",
                              (cass[0], posizione, progetto, tipo))
                    conn.commit()
                    st.success("Box aggiunto")

    with st.expander("Aggiungi nuovo cassetto"):
        numero = st.number_input("Numero cassetto", min_value=1, step=1)
        if st.button("Aggiungi cassetto"):
            c.execute("INSERT INTO cassetto (freezer_id, numero) VALUES (?, ?)", (freezer_id, numero))
            conn.commit()
            st.success("Cassetto aggiunto")
