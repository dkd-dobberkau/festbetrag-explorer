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
import json
import subprocess
import tempfile
from streamlit_searchbox import st_searchbox

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
            SELECT pzn, arzneimittelname, hersteller, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform, zuzahlungsbefreit
            FROM medications
            WHERE pzn LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'{query}%', limit)
    elif search_type == "name":
        sql = """
            SELECT pzn, arzneimittelname, hersteller, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform, zuzahlungsbefreit
            FROM medications
            WHERE arzneimittelname LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'%{query.upper()}%', limit)
    elif search_type == "wirkstoff":
        sql = """
            SELECT pzn, arzneimittelname, hersteller, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform, zuzahlungsbefreit
            FROM medications
            WHERE wirkstoff LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'%{query}%', limit)
    else:  # all
        sql = """
            SELECT pzn, arzneimittelname, hersteller, wirkstoff, packungsgroesse,
                   preis, festbetrag, differenz, darreichungsform, zuzahlungsbefreit
            FROM medications
            WHERE pzn LIKE ? OR arzneimittelname LIKE ? OR wirkstoff LIKE ?
            ORDER BY preis ASC
            LIMIT ?
        """
        params = (f'{query}%', f'%{query.upper()}%', f'%{query}%', limit)

    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()

    return df


def search_function(searchterm: str):
    """Searchbox callback function that returns suggestions."""
    if not searchterm or len(searchterm) < 2:
        return []

    # Get search type from session state
    search_type = st.session_state.get('search_type', 'all')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        if search_type == "pzn":
            cursor.execute("""
                SELECT DISTINCT pzn || ' - ' || arzneimittelname as suggestion
                FROM medications
                WHERE pzn LIKE ?
                ORDER BY pzn ASC
                LIMIT 15
            """, (f'{searchterm}%',))
        elif search_type == "name":
            cursor.execute("""
                SELECT DISTINCT arzneimittelname || ' (' || wirkstoff || ')' as suggestion
                FROM medications
                WHERE arzneimittelname LIKE ?
                ORDER BY arzneimittelname ASC
                LIMIT 15
            """, (f'%{searchterm.upper()}%',))
        elif search_type == "wirkstoff":
            cursor.execute("""
                SELECT DISTINCT wirkstoff as suggestion
                FROM medications
                WHERE wirkstoff LIKE ?
                ORDER BY wirkstoff ASC
                LIMIT 15
            """, (f'%{searchterm}%',))
        else:  # all
            cursor.execute("""
                SELECT DISTINCT
                    CASE
                        WHEN pzn LIKE ? THEN pzn || ' - ' || arzneimittelname
                        WHEN arzneimittelname LIKE ? THEN arzneimittelname || ' (' || wirkstoff || ')'
                        ELSE wirkstoff
                    END as suggestion
                FROM medications
                WHERE pzn LIKE ? OR arzneimittelname LIKE ? OR wirkstoff LIKE ?
                ORDER BY suggestion ASC
                LIMIT 15
            """, (f'{searchterm}%', f'%{searchterm.upper()}%', f'{searchterm}%', f'%{searchterm.upper()}%', f'%{searchterm}%'))

        results = [row[0] for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


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
        SELECT pzn, arzneimittelname, hersteller, wirkstoff, packungsgroesse,
               preis, festbetrag, differenz, darreichungsform, zuzahlungsbefreit
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


def initialize_watchlist():
    """Initialize watchlist in session state (session-only, no persistence)."""
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []

    # Check if we should load from uploaded file
    if 'uploaded_watchlist_data' in st.session_state and st.session_state.uploaded_watchlist_data:
        try:
            st.session_state.watchlist = json.loads(st.session_state.uploaded_watchlist_data)
            st.session_state.uploaded_watchlist_data = None  # Clear after loading
        except:
            pass


def add_to_watchlist(pzn, name, preis, festbetrag, hersteller=None, zuzahlungsbefreit=0):
    """Add medication to watchlist."""
    medication = {
        'pzn': pzn,
        'name': name,
        'preis': preis,
        'festbetrag': festbetrag,
        'hersteller': hersteller,
        'zuzahlungsbefreit': zuzahlungsbefreit
    }

    # Check if already in watchlist
    if not any(m['pzn'] == pzn for m in st.session_state.watchlist):
        st.session_state.watchlist.append(medication)
        return True
    return False


def remove_from_watchlist(pzn):
    """Remove medication from watchlist."""
    st.session_state.watchlist = [
        m for m in st.session_state.watchlist if m['pzn'] != pzn
    ]


def export_watchlist():
    """Export watchlist as JSON."""
    return json.dumps(st.session_state.watchlist, indent=2, ensure_ascii=False)


def import_watchlist(json_str):
    """Import watchlist from JSON."""
    try:
        st.session_state.watchlist = json.loads(json_str)
        return True
    except:
        return False


def run_pdf_import(pdf_file):
    """Run PDF import process with uploaded file."""
    try:
        # Save uploaded file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name

        # Run import script
        result = subprocess.run(
            ['python', 'scripts/import_zuzahlungsbefreit.py', tmp_path],
            capture_output=True,
            text=True,
            timeout=300
        )

        # Clean up
        os.unlink(tmp_path)

        return result.returncode == 0, result.stdout, result.stderr

    except Exception as e:
        return False, "", str(e)


def main():
    """Main app function."""
    st.title("💊 Festbetrag Explorer")
    st.markdown("**Finden Sie günstigere Medikamenten-Alternativen**")

    # Initialize watchlist (loads from file automatically)
    initialize_watchlist()

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
            }[x],
            key="search_type"
        )

        limit = st.slider("Max. Ergebnisse", 10, 200, 50)

        st.markdown("---")

        # Watchlist section
        st.markdown(f"### 📋 Meine Merkliste ({len(st.session_state.watchlist)})")

        if st.session_state.watchlist:
            for med in st.session_state.watchlist:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    # Add emoji for zuzahlungsbefreit
                    zb_icon = "🆓 " if med.get('zuzahlungsbefreit', 0) == 1 else ""
                    st.write(f"{zb_icon}**{med['name']}**")

                    # Show manufacturer if available
                    hersteller = med.get('hersteller')
                    if hersteller:
                        st.caption(f"🏭 {hersteller}")
                    st.caption(f"PZN: {med['pzn']} | {med['preis']:.2f}€")
                with col2:
                    if st.button("🔍", key=f"search_{med['pzn']}", help="Alternativen suchen"):
                        # Trigger search for this medication
                        st.session_state.selected_watchlist_pzn = med['pzn']
                        st.rerun()
                with col3:
                    if st.button("❌", key=f"remove_{med['pzn']}", help="Entfernen"):
                        remove_from_watchlist(med['pzn'])
                        st.rerun()

            # Download/Clear buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="💾 Download",
                    data=export_watchlist(),
                    file_name="merkliste.json",
                    mime="application/json"
                )
            with col2:
                if st.button("🗑️ Leeren"):
                    st.session_state.watchlist = []
                    st.rerun()

        else:
            st.info("Keine Medikamente in der Merkliste")

        # Upload watchlist (always visible)
        st.markdown("---")
        uploaded_watchlist = st.file_uploader("📤 Merkliste laden", type="json", key="watchlist_upload")
        if uploaded_watchlist is not None:
            try:
                content = uploaded_watchlist.read().decode()
                # Store in session state to load on next rerun
                st.session_state.uploaded_watchlist_data = content
                st.success("✅ Merkliste wird geladen...")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Fehler beim Laden: {e}")

        st.markdown("---")

        # Admin section
        if st.checkbox("🔧 Admin-Bereich"):
            st.markdown("### PDF Import")
            uploaded_pdf = st.file_uploader("PDF hochladen", type="pdf", key="pdf_upload")

            if uploaded_pdf and st.button("Import starten"):
                with st.spinner("Importiere PDF..."):
                    success, stdout, stderr = run_pdf_import(uploaded_pdf)

                    if success:
                        st.success("✅ Import erfolgreich!")
                        with st.expander("Details anzeigen"):
                            st.code(stdout)
                    else:
                        st.error("❌ Import fehlgeschlagen!")
                        with st.expander("Fehler anzeigen"):
                            st.code(stderr if stderr else stdout)

        st.markdown("---")
        st.markdown("### ℹ️ Info")
        st.markdown("""
        **Festbetrag**: Maximalbetrag, den die Krankenkasse erstattet.

        **Differenz**:
        - 🟢 Negativ: Unter Festbetrag (voll erstattet)
        - 🔴 Positiv: Über Festbetrag (Zuzahlung nötig)
        """)

    # Search box with inline autocomplete (always visible)
    selected_value = st_searchbox(
        search_function,
        placeholder="🔎 PZN, Medikamentenname oder Wirkstoff eingeben...",
        label="Medikament suchen",
        clear_on_submit=False,
        key="medication_searchbox"
    )

    # Determine search query
    search_query = None

    # Check if searching from watchlist
    if 'selected_watchlist_pzn' in st.session_state and st.session_state.selected_watchlist_pzn:
        # Search triggered from watchlist - use PZN directly
        search_query = st.session_state.selected_watchlist_pzn
        # Clear the trigger
        st.session_state.selected_watchlist_pzn = None
    elif selected_value:
        # Extract search query from searchbox value
        if " - " in selected_value:  # PZN format
            search_query = selected_value.split(" - ")[0]
        elif " (" in selected_value:  # Name format
            search_query = selected_value.split(" (")[0]
        else:  # Wirkstoff or direct input
            search_query = selected_value

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
            styled_df = df.style.map(
                color_differenz,
                subset=['differenz']
            ).format({
                'preis': '{:.2f}€',
                'festbetrag': '{:.2f}€',
                'differenz': '{:.2f}€'
            })

            st.dataframe(styled_df, use_container_width=True, height=400)

            # Add to watchlist buttons
            st.markdown("### ➕ Zur Merkliste hinzufügen")
            cols = st.columns(min(len(df), 5))
            for idx, (_, row) in enumerate(df.head(5).iterrows()):
                with cols[idx]:
                    if st.button(
                        f"➕ {row['arzneimittelname'][:15]}...",
                        key=f"add_{row['pzn']}",
                        use_container_width=True
                    ):
                        if add_to_watchlist(
                            row['pzn'],
                            row['arzneimittelname'],
                            row['preis'],
                            row['festbetrag'],
                            row.get('hersteller'),
                            row.get('zuzahlungsbefreit', 0)
                        ):
                            st.success(f"✅ Hinzugefügt!")
                            st.rerun()
                        else:
                            st.warning("Bereits in Merkliste")

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

                    styled_alt = alt_df.style.map(
                        color_differenz,
                        subset=['differenz']
                    ).format({
                        'preis': '{:.2f}€',
                        'festbetrag': '{:.2f}€',
                        'differenz': '{:.2f}€'
                    })

                    st.dataframe(styled_alt, use_container_width=True)

                    # Add to watchlist buttons for alternatives
                    st.markdown("### ➕ Alternative zur Merkliste hinzufügen")

                    # Show top 5 cheapest alternatives
                    top_alternatives = alt_df.nsmallest(5, 'preis')
                    cols = st.columns(min(len(top_alternatives), 5))

                    for idx, (_, row) in enumerate(top_alternatives.iterrows()):
                        with cols[idx]:
                            # Show price and savings
                            price_info = f"{row['preis']:.2f}€"
                            if row['preis'] < original_price:
                                savings_per_pack = original_price - row['preis']
                                price_info += f" (-{savings_per_pack:.2f}€)"

                            # Add zuzahlungsbefreit indicator
                            zb_indicator = "🆓 " if row.get('zuzahlungsbefreit', 0) == 1 else ""

                            if st.button(
                                f"{zb_indicator}➕ {row['arzneimittelname'][:20]}...",
                                key=f"add_alt_{row['pzn']}",
                                use_container_width=True,
                                help=f"{row['arzneimittelname']}\n{price_info}"
                            ):
                                if add_to_watchlist(
                                    row['pzn'],
                                    row['arzneimittelname'],
                                    row['preis'],
                                    row['festbetrag'],
                                    row.get('hersteller'),
                                    row.get('zuzahlungsbefreit', 0)
                                ):
                                    st.success(f"✅ Hinzugefügt!")
                                    st.rerun()
                                else:
                                    st.warning("Bereits in Merkliste")

                            # Show price below button
                            st.caption(price_info)
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
