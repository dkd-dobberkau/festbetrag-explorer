#!/usr/bin/env python3
"""
Festbetrag Explorer - Streamlit App
Einfache Suche und Vergleich von Medikamenten basierend auf der Festbetragsliste.
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import os

# Page config
st.set_page_config(
    page_title="Festbetrag Explorer",
    page_icon="💊",
    layout="wide"
)

# Database path
DB_PATH = Path(__file__).parent / "data" / "festbetrag.db"


def check_database():
    """Check if database exists and has data."""
    if not DB_PATH.exists():
        st.error("❌ Keine Datenbank gefunden!")
        st.info("""
        📋 **So richten Sie die Datenbank ein:**
        1. Laden Sie die Festbetragsliste vom GKV-Spitzenverband herunter
        2. Extrahieren Sie die Daten mit dem bereitgestellten Import-Script
        3. Legen Sie die `festbetrag.db` im `data/` Verzeichnis ab

        Siehe README.md für detaillierte Anleitung.
        """)
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM medications")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            st.warning("⚠️ Datenbank ist leer!")
            return False

        return True
    except Exception as e:
        st.error(f"❌ Fehler beim Zugriff auf Datenbank: {e}")
        return False


def search_medications(query, search_type="all", limit=50):
    """Search for medications in database."""
    conn = sqlite3.connect(DB_PATH)

    if search_type == "pzn":
        sql = """
            SELECT pzn, arzneimittelname, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform
            FROM medications
            WHERE pzn LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'{query}%', limit)
    elif search_type == "name":
        sql = """
            SELECT pzn, arzneimittelname, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform
            FROM medications
            WHERE arzneimittelname LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'%{query.upper()}%', limit)
    elif search_type == "wirkstoff":
        sql = """
            SELECT pzn, arzneimittelname, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform
            FROM medications
            WHERE wirkstoff LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'%{query}%', limit)
    else:  # all
        sql = """
            SELECT pzn, arzneimittelname, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform
            FROM medications
            WHERE pzn LIKE ? OR arzneimittelname LIKE ? OR wirkstoff LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'{query}%', f'%{query.upper()}%', f'%{query}%', limit)

    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()

    return df


def get_alternatives(pzn):
    """Get cheaper alternatives for a medication."""
    conn = sqlite3.connect(DB_PATH)

    # Get original medication
    cursor = conn.cursor()
    cursor.execute("""
        SELECT festbetragsgruppe, wirkstoffmenge_1, wirkstoffmenge_2,
               packungsgroesse, darreichungsform
        FROM medications
        WHERE pzn = ?
    """, (pzn,))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return pd.DataFrame()

    gruppe, menge1, menge2, package, form = result

    # Find alternatives
    sql = """
        SELECT pzn, arzneimittelname, wirkstoff, packungsgroesse,
               preis, festbetrag, differenz, darreichungsform
        FROM medications
        WHERE festbetragsgruppe = ?
            AND wirkstoffmenge_1 = ?
            AND wirkstoffmenge_2 = ?
            AND packungsgroesse = ?
            AND darreichungsform = ?
        ORDER BY preis ASC
        LIMIT 20
    """

    df = pd.read_sql_query(sql, conn, params=(gruppe, menge1, menge2, package, form))
    conn.close()

    return df


def main():
    """Main app function."""
    st.title("💊 Festbetrag Explorer")
    st.markdown("**Finden Sie günstigere Medikamenten-Alternativen**")

    # Check database
    if not check_database():
        return

    # Sidebar for search options
    with st.sidebar:
        st.header("🔍 Suchoptionen")
        search_type = st.radio(
            "Suchen nach:",
            ["all", "pzn", "name", "wirkstoff"],
            format_func=lambda x: {
                "all": "Alles",
                "pzn": "PZN",
                "name": "Medikamentenname",
                "wirkstoff": "Wirkstoff"
            }[x]
        )

        limit = st.slider("Max. Ergebnisse", 10, 200, 50)

        st.markdown("---")
        st.markdown("### ℹ️ Info")
        st.markdown("""
        **Festbetrag**: Maximalbetrag, den die Krankenkasse erstattet.

        **Differenz**:
        - 🟢 Negativ: Unter Festbetrag (voll erstattet)
        - 🔴 Positiv: Über Festbetrag (Zuzahlung nötig)
        """)

    # Search box
    search_query = st.text_input(
        "🔎 Medikament suchen",
        placeholder="PZN, Medikamentenname oder Wirkstoff eingeben..."
    )

    if search_query:
        with st.spinner("Suche läuft..."):
            df = search_medications(search_query, search_type, limit)

        if df.empty:
            st.warning("Keine Ergebnisse gefunden.")
        else:
            st.success(f"✅ {len(df)} Ergebnisse gefunden")

            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Günstigster", f"{df['preis'].min():.2f}€")
            with col2:
                st.metric("Teuerster", f"{df['preis'].max():.2f}€")
            with col3:
                st.metric("Durchschnitt", f"{df['preis'].mean():.2f}€")
            with col4:
                if not df.empty:
                    st.metric("Festbetrag", f"{df['festbetrag'].iloc[0]:.2f}€")

            # Color code by differenz
            def color_differenz(val):
                if val < 0:
                    return 'background-color: #d4edda'  # green
                elif val > 0:
                    return 'background-color: #f8d7da'  # red
                else:
                    return 'background-color: #fff3cd'  # yellow

            # Format dataframe
            styled_df = df.style.applymap(
                color_differenz,
                subset=['differenz']
            ).format({
                'preis': '{:.2f}€',
                'festbetrag': '{:.2f}€',
                'differenz': '{:.2f}€'
            })

            st.dataframe(styled_df, use_container_width=True, height=400)

            # Show alternatives for selected medication
            st.markdown("---")
            st.subheader("🔄 Günstigere Alternativen finden")

            selected_pzn = st.selectbox(
                "Wählen Sie ein Medikament für Alternativen-Suche:",
                options=df['pzn'].tolist(),
                format_func=lambda x: f"{x} - {df[df['pzn']==x]['arzneimittelname'].iloc[0]}"
            )

            if selected_pzn:
                alt_df = get_alternatives(selected_pzn)

                if not alt_df.empty:
                    original_price = df[df['pzn']==selected_pzn]['preis'].iloc[0]
                    cheapest_price = alt_df['preis'].min()
                    savings = original_price - cheapest_price

                    if savings > 0:
                        st.success(f"💰 Einsparpotenzial: **{savings:.2f}€** pro Packung")

                    styled_alt = alt_df.style.applymap(
                        color_differenz,
                        subset=['differenz']
                    ).format({
                        'preis': '{:.2f}€',
                        'festbetrag': '{:.2f}€',
                        'differenz': '{:.2f}€'
                    })

                    st.dataframe(styled_alt, use_container_width=True)
                else:
                    st.info("Keine Alternativen gefunden.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    <p>⚠️ Haftungsausschluss: Diese App dient nur zu Informationszwecken.
    Konsultieren Sie immer Ihren Arzt oder Apotheker vor einer Medikamentenänderung.</p>
    <p>Datenquelle: GKV-Spitzenverband Festbetragsliste</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
