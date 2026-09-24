import os
import random
import re
import sqlite3

import pandas as pd
import streamlit as st

from dashboard import render_dashboard


# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(
    page_title="Opus Observer",
    page_icon="🎵",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "songs.db")
COVERS_DIR = os.path.join(BASE_DIR, "covers")


# ==========================================
# 2. Data Loading & State Management
# ==========================================
@st.cache_data
def load_data():
    """Load songs from database and normalize columns."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM songs", conn)
    conn.close()

    if "Rating" in df.columns:
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)

    return df


try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error reading database at `{DB_PATH}`: {e}")
    st.stop()

if "id" in df_raw.columns:
    ID_COL = "id"
elif "ID" in df_raw.columns:
    ID_COL = "ID"
else:
    df_raw["id"] = df_raw.index
    ID_COL = "id"

if "selections" not in st.session_state:
    st.session_state.selections = {song_id: False for song_id in df_raw[ID_COL]}

filtered_df = df_raw.copy()


# ==========================================
# 3. Helper Functions
# ==========================================
def get_column_name(candidates):
    """Find first available column from a list of candidates."""
    for col in candidates:
        if col in df_raw.columns:
            return col
    return None


def clean_series(series):
    """Remove empty strings, 'nan', and 'N/A' values from a series."""
    cleaned = series.astype(str).str.split(",").explode().str.strip()
    cleaned = cleaned[~cleaned.isin(["", "nan", "N/A"])]
    return cleaned


def list_to_regex_pattern(items):
    """Convert a list of strings to a regex OR pattern, or return None if empty."""
    if not items:
        return None
    if isinstance(items, list):
        escaped_items = [re.escape(str(item)) for item in items]
        return "|".join(escaped_items)
    return str(items)


def generate_m3u_playlist(selected_songs_df, output_path):
    """Generate M3U playlist file from selected songs."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for idx, row in selected_songs_df.iterrows():
            title = row.get("Title", "Unknown")
            artist = row.get("Artist", "Unknown")
            f.write(f"#EXTINF:-1,{artist} - {title}\n")
            f.write(f"{title}.mp3\n")
    return output_path


def generate_pls_playlist(selected_songs_df, output_path):
    """Generate PLS playlist file from selected songs."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("[playlist]\n")
        for idx, row in selected_songs_df.iterrows():
            file_num = idx + 1
            title = row.get("Title", "Unknown")
            artist = row.get("Artist", "Unknown")
            f.write(f"File{file_num}={title}.mp3\n")
            f.write(f"Title{file_num}={artist} - {title}\n")
            f.write(f"Length{file_num}=-1\n")
        f.write(f"\nNumberOfEntries={len(selected_songs_df)}\n")
        f.write("Version=2\n")
    return output_path


@st.cache_data
def get_running_banner_facts(total_songs=0, top_comp="", top_comp_count=0, top_lyr="", oldest_yr="", newest_yr=""):
    """Generate collection insights for the running banner."""
    general_facts = [
        f"🏆 Top Composer: {top_comp} has {top_comp_count} songs in your collection.",
        f"✍️ Top Lyricist: {top_lyr} is your most featured writer.",
        f"📅 History: Your database spans from {oldest_yr} to {newest_yr}.",
        f"📂 Collection Size: You are currently managing {total_songs} tracks.",
    ]
    return general_facts


def render_opus_observer_header_with_banner(df: pd.DataFrame):
    """Render animated header and running ticker banner."""
    if df.empty:
        facts = ["🎵 Welcome to Opus Observer!"]
    else:
        total_songs = len(df)
        col_comp = get_column_name(["Composer", "Music Director", "Music"])
        col_lyr = get_column_name(["Lyricist", "Lyrics", "Writer"])
        col_year = get_column_name(["Year", "Release Year", "Yr"])

        top_comp, top_comp_count = "N/A", 0
        if col_comp and not df[col_comp].dropna().empty:
            comp_series = clean_series(df[col_comp])
            if not comp_series.empty:
                counts = comp_series.value_counts()
                top_comp = counts.index[0]
                top_comp_count = int(counts.iloc[0])

        top_lyr = "N/A"
        if col_lyr and not df[col_lyr].dropna().empty:
            lyr_series = clean_series(df[col_lyr])
            if not lyr_series.empty:
                top_lyr = lyr_series.value_counts().index[0]

        oldest_yr, newest_yr = "N/A", "N/A"
        if col_year:
            valid_years = pd.to_numeric(df[col_year], errors="coerce").dropna()
            valid_years = valid_years[valid_years > 0]
            if not valid_years.empty:
                oldest_yr = int(valid_years.min())
                newest_yr = int(valid_years.max())

        facts = get_running_banner_facts(total_songs, top_comp, top_comp_count, top_lyr, oldest_yr, newest_yr)

    selected_facts = random.sample(facts, k=min(len(facts), 4))
    ticker_text = " • ".join(selected_facts)

    st.markdown(
        """
        <style>
        .opus-header {
            font-size: 2.6rem;
            font-weight: 800;
            text-align: center;
            color: #0F172A;
            margin-top: 10px;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
        }

        .marquee-container {
            width: 100%;
            min-height: 44px;
            line-height: 44px;
            overflow: hidden;
            white-space: nowrap;
            background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
            color: #F8FAFC;
            border-radius: 8px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.12);
            margin-bottom: 24px;
            border-left: 4px solid #3B82F6;
        }

        .marquee-track {
            display: inline-block;
            white-space: nowrap;
            padding-left: 100%;
            animation: marquee 90s linear infinite;
            font-size: 0.95rem;
            font-weight: 500;
        }

        @keyframes marquee {
            0% { transform: translate(0, 0); }
            100% { transform: translate(-100%, 0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="opus-header">🕺✨🎧🎵 Opus Observer 🎶💃✨🎶</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="marquee-container">
            <div class="marquee-track">
                {ticker_text} • {ticker_text} • {ticker_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# 4. Render Header
# ==========================================
render_opus_observer_header_with_banner(df_raw)


# ==========================================
# 5. Sidebar Filters
# ==========================================
st.sidebar.header("🔍 Filter Catalog")

if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("filter_")]
    for key in keys_to_delete:
        del st.session_state[key]
    if "song_editor" in st.session_state:
        del st.session_state["song_editor"]
    st.rerun()

if "Rating" in df_raw.columns:
    min_rating = int(df_raw["Rating"].min())
    max_rating = int(df_raw["Rating"].max())

    if min_rating < max_rating:
        selected_rating = st.sidebar.slider(
            "Rating",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
            key="filter_rating",
        )
        filtered_df = filtered_df[
            (filtered_df["Rating"] >= selected_rating[0])
            & (filtered_df["Rating"] <= selected_rating[1])
        ]

filter_attributes = [
    "Album",
    "Year",
    "Lyricist",
    "Artist",
    "Composer",
    "Genre",
    "Language",
    "Mood",
    "Poetic Depth",
    "Orchestration",
    "Cohesion",
]

selected_filters = {}

for attr in filter_attributes:
    if attr in df_raw.columns:
        available_options = sorted(
            [
                str(x)
                for x in filtered_df[attr].dropna().unique()
                if str(x).strip() != ""
            ]
        )

        selected = st.sidebar.multiselect(
            label=attr,
            options=available_options,
            key=f"filter_{attr}",
        )

        selected_filters[attr] = selected if selected else None

        if selected:
            filtered_df = filtered_df[filtered_df[attr].astype(str).isin(selected)]
    else:
        selected_filters[attr] = None

sel_artist = list_to_regex_pattern(selected_filters.get("Artist"))
sel_composer = list_to_regex_pattern(selected_filters.get("Composer"))
sel_lyricist = list_to_regex_pattern(selected_filters.get("Lyricist"))
sel_language = list_to_regex_pattern(selected_filters.get("Language"))
sel_genre = list_to_regex_pattern(selected_filters.get("Genre"))
sel_year = list_to_regex_pattern(selected_filters.get("Year"))


# ==========================================
# 6. Dashboard Call (CACHED)
# ==========================================
with st.spinner("📊 Loading analytics..."):
    render_dashboard(
        df=df_raw,
        sel_artist=sel_artist,
        sel_composer=sel_composer,
        sel_lyricist=sel_lyricist,
        sel_language=sel_language,
        sel_genre=sel_genre,
        sel_year=sel_year,
    )


# ==========================================
# 7. Results Table (Select checkbox only)
# ==========================================
col_header, col_btn_select, col_btn_clear = st.columns([2, 1, 1])

with col_header:
    st.subheader(f"📋 Filtered Results ({len(filtered_df)} / {len(df_raw)} songs)")

with col_btn_select:
    if st.button("✅ Select Filtered", use_container_width=True):
        for song_id in filtered_df[ID_COL]:
            st.session_state.selections[song_id] = True
        st.rerun()

with col_btn_clear:
    if st.button("🧹 Clear Selections", use_container_width=True):
        st.session_state.selections = {song_id: False for song_id in df_raw[ID_COL]}
        st.rerun()

target_columns = [
    "Rating",
    "Album",
    "Title",
    "Year",
    "Artist",
    "Co-Artist",
    "Composer",
    "Lyricist",
    "Genre",
    "Mood",
    "Poetic Depth",
    "Orchestration",
    "Cohesion",
]

available_cols = [c for c in target_columns if c in filtered_df.columns]

filtered_df["Select"] = filtered_df[ID_COL].map(st.session_state.selections)

display_cols = [ID_COL, "Select"] + available_cols
display_df = filtered_df[display_cols]

edited_df = st.data_editor(
    display_df,
    hide_index=True,
    use_container_width=True,
    height=600,
    disabled=[c for c in display_cols if c != "Select"],
    column_config={
        ID_COL: None,
        "Select": st.column_config.CheckboxColumn(
            "Select",
            help="Check to select song",
            default=False,
        ),
    },
    key="song_editor",
)

st.session_state.selections.update(
    dict(zip(edited_df[ID_COL], edited_df["Select"]))
)

selected_count = sum(st.session_state.selections.values())

if selected_count > 0:
    st.info(f"🎵 **{selected_count}** track(s) currently selected across library.")


# ==========================================
# 8. ULTRA-COMPACT AUDIO PLAYER VIEW
# ==========================================
if selected_count > 0:
    st.markdown("---")
    st.subheader("▶️ Play Your Selected Songs")
    
    selected_song_ids_list = [idx for idx, selected in st.session_state.selections.items() if selected]
    selected_songs_play = df_raw[df_raw[ID_COL].isin(selected_song_ids_list)].copy()
    
    def get_cover_image_path(song_id, title, artist):
        """
        Look for cover image in covers/ folder.
        Naming convention: {song_id:05d}_{artist}_{title}.jpg
        song_id should be a zero-padded 5-digit number (from DataFrame index).
        """
        if not os.path.exists(COVERS_DIR):
            return None
        
        # Sanitize filename parts (same logic as extraction script)
        try:
            safe_title = str(title).replace("/", "_").replace("\\", "_").replace(":", "_")
            safe_artist = str(artist).replace("/", "_").replace("\\", "_").replace(":", "_")
            
            # Build expected filename (with padding and file extension)
            filename_prefix = f"{int(song_id):05d}_{safe_artist}_{safe_title}"
            
            # Look for any image with this prefix (may have different extensions)
            covers = [f for f in os.listdir(COVERS_DIR) if f.startswith(filename_prefix)]
            
            if covers:
                return os.path.join(COVERS_DIR, covers[0])
        except:
            pass
        
        return None
    
    for idx, row in selected_songs_play.iterrows():
        # Get all metadata
        title = row.get("Title", "Unknown")
        artist = row.get("Artist", "Unknown")
        year = row.get("Year", "")
        language = row.get("Language", "N/A")
        album = row.get("Album", "N/A")
        co_artist = row.get("Co-Artist", "N/A")
        composer = row.get("Composer", "N/A")
        lyricist = row.get("Lyricist", "N/A")
        genre = row.get("Genre", "N/A")
        song_id = idx  # Use DataFrame index (0-based, matches cover naming: 00000, 00001, ...)
        mood = row.get("Mood", "N/A")
        trivia = row.get("Trivia", "")
        rating = row.get("Rating", "N/A")
        poetic_depth = row.get("Poetic Depth", "N/A")
        orchestration = row.get("Orchestration", "N/A")
        resonance = row.get("Resonance", "N/A")
        obsession = row.get("Obsession", "N/A")
        signature = row.get("Signature", "N/A")
        cohesion = row.get("Cohesion", "N/A")
        
        # Ultra-compact metadata in expander - all in one line header
        with st.expander(f"🎵 {title} — {artist} • {album}", expanded=False):
            # Cover art + metadata side-by-side
            cover_path = get_cover_image_path(song_id, title, artist)
            
            if cover_path and os.path.exists(cover_path):
                col_cover, col_metadata = st.columns([1, 3])
                
                with col_cover:
                    st.image(cover_path, width=120)
                
                with col_metadata:
                    # Song details - ONE line
                    st.markdown(
                        f"🎤 {artist} | 🎼 {composer} | ✍️ {lyricist} | 🎙️ {album} | 🌍 {language} | 🎸 {genre} | 😊 {mood}"
                    )
                    
                    # Ratings - ONE line
                    st.markdown(
                        f"⭐ {rating} | 📝 {poetic_depth} | 🎵 {orchestration} | 💫 {resonance} | 🔥 {obsession} | ✨ {signature} | 🎼 {cohesion}"
                    )
            else:
                # No cover art available - show metadata only
                # Song details - ONE line
                st.markdown(
                    f"🎤 {artist} | 🎼 {composer} | ✍️ {lyricist} | 🎙️ {album} | 🌍 {language} | 🎸 {genre} | 😊 {mood}"
                )
                
                # Ratings - ONE line
                st.markdown(
                    f"⭐ {rating} | 📝 {poetic_depth} | 🎵 {orchestration} | 💫 {resonance} | 🔥 {obsession} | ✨ {signature} | 🎼 {cohesion}"
                )
            
            
            if co_artist and str(co_artist).strip() not in ["", "nan", "N/A"]:
                st.markdown(f"🎵 Co-Artist: {co_artist}")
            
            # Trivia only if exists (no duplicate ratings)
            if trivia and str(trivia).strip() not in ["", "nan", "N/A"]:
                st.info(f"💡 {trivia}")
            
        # Audio player - minimal spacing
        path_dir = row.get("Path", "")
        filename = row.get("Filename", "")
        
        if path_dir and filename:
            audio_path = os.path.join(path_dir, filename)
            
            if os.path.exists(audio_path):
                try:
                    audio_bytes = open(audio_path, 'rb').read()
                    st.audio(audio_bytes, format="audio/mp3")
                except Exception as e:
                    st.error(f"❌ {type(e).__name__}")


# ==========================================
# 9. PLAYLIST GENERATION
# ==========================================
if selected_count > 0:
    st.divider()
    st.subheader("🎧 Create Playlist from Selection")
    
    selected_song_ids = [idx for idx, selected in st.session_state.selections.items() if selected]
    selected_songs_df = df_raw[df_raw[ID_COL].isin(selected_song_ids)].copy()
    
    st.write("**Step 1: Name Your Playlist**")
    playlist_name = st.text_input(
        "📝 Enter Playlist Name",
        placeholder="e.g., my_fav_rock_songs, romantic_list, chill_vibes",
        help="Enter a custom name for your playlist"
    )
    
    safe_name = playlist_name.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    if not safe_name:
        safe_name = None
    
    if safe_name:
        st.write(f"**Step 2: Generate Format** (Playlist name: `{safe_name}`)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📁 Generate M3U", use_container_width=True, key="btn_m3u"):
                m3u_filename = f"{safe_name}.m3u"
                m3u_path = m3u_filename
                generate_m3u_playlist(selected_songs_df, m3u_path)
                
                with open(m3u_path, 'r', encoding='utf-8') as f:
                    m3u_data = f.read()
                
                st.session_state.m3u_data = m3u_data
                st.session_state.m3u_filename = m3u_filename
                st.success(f"✅ M3U ready: {m3u_filename}")
        
        with col2:
            if st.button("📁 Generate PLS", use_container_width=True, key="btn_pls"):
                pls_filename = f"{safe_name}.pls"
                pls_path = pls_filename
                generate_pls_playlist(selected_songs_df, pls_path)
                
                with open(pls_path, 'r', encoding='utf-8') as f:
                    pls_data = f.read()
                
                st.session_state.pls_data = pls_data
                st.session_state.pls_filename = pls_filename
                st.success(f"✅ PLS ready: {pls_filename}")
        
        with col3:
            if st.button("📊 Export CSV", use_container_width=True, key="btn_csv"):
                csv_filename = f"{safe_name}_songs.csv"
                csv_data = selected_songs_df.to_csv(index=False)
                
                st.session_state.csv_data = csv_data
                st.session_state.csv_filename = csv_filename
                st.success(f"✅ CSV ready: {csv_filename}")
        
        st.markdown("---")
        st.write("**Step 3: Download Your File**")
        
        download_cols = st.columns(3)
        
        if hasattr(st.session_state, 'm3u_data') and st.session_state.m3u_data:
            with download_cols[0]:
                st.download_button(
                    label="⬇️ Download M3U",
                    data=st.session_state.m3u_data,
                    file_name=st.session_state.m3u_filename,
                    mime="audio/x-mpegurl",
                    key="dl_m3u"
                )
        
        if hasattr(st.session_state, 'pls_data') and st.session_state.pls_data:
            with download_cols[1]:
                st.download_button(
                    label="⬇️ Download PLS",
                    data=st.session_state.pls_data,
                    file_name=st.session_state.pls_filename,
                    mime="audio/x-scpls",
                    key="dl_pls"
                )
        
        if hasattr(st.session_state, 'csv_data') and st.session_state.csv_data:
            with download_cols[2]:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=st.session_state.csv_data,
                    file_name=st.session_state.csv_filename,
                    mime="text/csv",
                    key="dl_csv"
                )
    else:
        st.info("👆 Enter a playlist name above to generate files")
