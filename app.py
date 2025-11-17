#!/usr/bin/env python3
"""
Festbetrag Explorer - Streamlit App
Einfache Suche und Vergleich von Medikamenten basierend auf der Festbetragsliste.
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import json
from streamlit_searchbox import st_searchbox
from utils.darreichungsformen import get_darreichungsform_with_abbr
from utils.packungsgroessen import (
    get_packungsgroesse_with_beschreibung,
    get_packungsgroesse_n,
    get_packungsgroesse_emoji
)

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


def format_darreichungsform(df):
    """Format darreichungsform column with long names and add N-Größe with emoji."""
    # Make a copy to avoid mutation issues
    df = df.copy()

    # ERST N-Größe berechnen (benötigt Original-Kürzel)
    if 'packungsgroesse' in df.columns and 'darreichungsform' in df.columns:
        # N-Größe berechnen mit Original-Kürzeln und Emoji hinzufügen
        def format_n_groesse(row):
            pkg = row['packungsgroesse'] if pd.notna(row['packungsgroesse']) else 0
            dform = row['darreichungsform'] if pd.notna(row['darreichungsform']) else ''

            n_text = get_packungsgroesse_with_beschreibung(pkg, dform)
            if not n_text:
                return ""

            # Extract N-Größe (N1, N2, N3) from text
            n_size = n_text.split()[0]  # "N3" from "N3 (Großpackung)"
            emoji = get_packungsgroesse_emoji(n_size)

            return f"{emoji} {n_text}" if emoji else n_text

        df['n_groesse'] = df.apply(format_n_groesse, axis=1)

        # Spalte nach packungsgroesse verschieben
        cols = list(df.columns)
        pkg_idx = cols.index('packungsgroesse')
        cols.remove('n_groesse')
        cols.insert(pkg_idx + 1, 'n_groesse')
        df = df[cols]

    # DANN Darreichungsform formatieren
    if 'darreichungsform' in df.columns:
        df['darreichungsform'] = df['darreichungsform'].apply(get_darreichungsform_with_abbr)

    return df


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

    return format_darreichungsform(df)


def search_function(searchterm: str):
    """Searchbox callback function that returns suggestions with N-Größe."""
    if not searchterm or len(searchterm) < 2:
        return []

    # Get search type from session state
    search_type = st.session_state.get('search_type', 'all')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        if search_type == "pzn":
            cursor.execute("""
                SELECT DISTINCT pzn, arzneimittelname, packungsgroesse, darreichungsform, preis
                FROM medications
                WHERE pzn LIKE ?
                ORDER BY pzn ASC
                LIMIT 15
            """, (f'{searchterm}%',))
            results = []
            for row in cursor.fetchall():
                pzn, name, pkg, dform, preis = row
                n_size = get_packungsgroesse_n(pkg, dform) if pkg and dform else ""
                n_tag = f" [{n_size}]" if n_size else ""
                results.append(f"{pzn} - {name}{n_tag} - {preis:.2f}€")
            return results

        elif search_type == "name":
            cursor.execute("""
                SELECT DISTINCT arzneimittelname, wirkstoff, packungsgroesse, darreichungsform, preis
                FROM medications
                WHERE arzneimittelname LIKE ?
                ORDER BY arzneimittelname ASC
                LIMIT 15
            """, (f'%{searchterm.upper()}%',))
            results = []
            for row in cursor.fetchall():
                name, wirkstoff, pkg, dform, preis = row
                n_size = get_packungsgroesse_n(pkg, dform) if pkg and dform else ""
                n_tag = f" [{n_size}]" if n_size else ""
                results.append(f"{name} ({wirkstoff}){n_tag} - {preis:.2f}€")
            return results

        elif search_type == "wirkstoff":
            cursor.execute("""
                SELECT DISTINCT wirkstoff
                FROM medications
                WHERE wirkstoff LIKE ?
                ORDER BY wirkstoff ASC
                LIMIT 15
            """, (f'%{searchterm}%',))
            results = [row[0] for row in cursor.fetchall()]
            return results

        else:  # all
            cursor.execute("""
                SELECT DISTINCT
                    pzn, arzneimittelname, wirkstoff, packungsgroesse, darreichungsform, preis,
                    CASE
                        WHEN pzn LIKE ? THEN 1
                        WHEN arzneimittelname LIKE ? THEN 2
                        ELSE 3
                    END as match_type
                FROM medications
                WHERE pzn LIKE ? OR arzneimittelname LIKE ? OR wirkstoff LIKE ?
                ORDER BY match_type ASC, arzneimittelname ASC
                LIMIT 15
            """, (f'{searchterm}%', f'%{searchterm.upper()}%', f'{searchterm}%', f'%{searchterm.upper()}%', f'%{searchterm}%'))

            results = []
            for row in cursor.fetchall():
                pzn, name, wirkstoff, pkg, dform, preis, match_type = row
                n_size = get_packungsgroesse_n(pkg, dform) if pkg and dform else ""
                n_tag = f" [{n_size}]" if n_size else ""

                if match_type == 1:  # PZN match
                    results.append(f"{pzn} - {name}{n_tag} - {preis:.2f}€")
                elif match_type == 2:  # Name match
                    results.append(f"{name} ({wirkstoff}){n_tag} - {preis:.2f}€")
                else:  # Wirkstoff match
                    results.append(wirkstoff)
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

    return format_darreichungsform(df)


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
                    st.caption(f"**PZN:** {med['pzn']}")

                    # Show manufacturer if available
                    hersteller = med.get('hersteller')
                    if hersteller:
                        st.caption(f"🏭 {hersteller}")
                    st.caption(f"💰 Preis: {med['preis']:.2f}€ | Festbetrag: {med['festbetrag']:.2f}€")
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
        # Handle new format with [N1/N2/N3] and price
        # Format examples:
        # - "12345678 - Medikamentenname [N3] - 5,49€"
        # - "Medikamentenname (Wirkstoff) [N3] - 5,49€"
        # - "Wirkstoff"

        # First, remove price if present (everything after last " - " followed by digits)
        clean_value = selected_value
        if " - " in clean_value and "€" in clean_value:
            # Remove the price part (last " - XX,XX€")
            parts = clean_value.rsplit(" - ", 1)
            if len(parts) == 2 and "€" in parts[1]:
                clean_value = parts[0]

        # Remove N-Größe if present [N1/N2/N3]
        if " [N" in clean_value:
            clean_value = clean_value.split(" [N")[0]

        # Now extract the actual search term
        if " - " in clean_value:  # PZN format
            search_query = clean_value.split(" - ")[0]
        elif " (" in clean_value:  # Name format
            search_query = clean_value.split(" (")[0]
        else:  # Wirkstoff or direct input
            search_query = clean_value

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

            # Reorder columns for better display
            column_order = [
                'arzneimittelname',
                'n_groesse',
                'darreichungsform',
                'packungsgroesse',
                'preis',
                'festbetrag',
                'differenz',
                'wirkstoff',
                'hersteller',
                'pzn',
                'zuzahlungsbefreit'
            ]
            # Only include columns that exist
            display_columns = [col for col in column_order if col in df.columns]
            df_display = df[display_columns]

            # Format dataframe
            styled_df = df_display.style.map(
                color_differenz,
                subset=['differenz']
            ).format({
                'preis': '{:.2f}€',
                'festbetrag': '{:.2f}€',
                'differenz': '{:.2f}€'
            })

            # Column configuration for better display
            column_config = {
                'arzneimittelname': st.column_config.TextColumn('Arzneimittel', width='large'),
                'n_groesse': st.column_config.TextColumn('N-Größe', width='small'),
                'darreichungsform': st.column_config.TextColumn('Darreichungsform', width='medium'),
                'packungsgroesse': st.column_config.NumberColumn('Pkg.', width='small'),
                'preis': st.column_config.TextColumn('Preis', width='small'),
                'festbetrag': st.column_config.TextColumn('Festbetrag', width='small'),
                'differenz': st.column_config.TextColumn('Differenz', width='small'),
                'wirkstoff': st.column_config.TextColumn('Wirkstoff', width='medium'),
                'hersteller': st.column_config.TextColumn('Hersteller', width='medium'),
                'pzn': st.column_config.TextColumn('PZN', width='small'),
                'zuzahlungsbefreit': st.column_config.CheckboxColumn('🆓 ZB', width='small')
            }

            st.dataframe(
                styled_df,
                use_container_width=True,
                height=400,
                column_config=column_config
            )

            # Add to watchlist buttons
            st.markdown("### ➕ Zur Merkliste hinzufügen")
            cols = st.columns(min(len(df), 5))
            for idx, (_, row) in enumerate(df.head(5).iterrows()):
                with cols[idx]:
                    # Show price info
                    price_info = f"{row['preis']:.2f}€"

                    # Add zuzahlungsbefreit indicator
                    zb_indicator = "🆓 " if row.get('zuzahlungsbefreit', 0) == 1 else ""

                    if st.button(
                        f"{zb_indicator}➕ {row['arzneimittelname'][:15]}...",
                        key=f"add_{row['pzn']}",
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
