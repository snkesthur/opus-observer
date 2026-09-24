import pandas as pd
import streamlit as st


# --- HELPER FUNCTIONS FOR FILTERED STATS ---
def _split_and_top(series, top_n=1):
    """Splits comma-separated strings, strips whitespace, and gets top value(s)."""
    if series.empty or series.dropna().empty:
        return "N/A"

    items = (
        series.dropna()
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
    )
    items = items[(items != "") & (items != "N/A")]

    if items.empty:
        return "N/A"

    counts = items.value_counts()
    if top_n == 1:
        return f"{counts.index[0]} ({counts.iloc[0]})"
    else:
        top_items = [f"{idx} ({val})" for idx, val in counts.head(top_n).items()]
        return ", ".join(top_items)


def _get_top_stat(df, column_name, suffix=""):
    """Calculates top occurrence and count for a column."""
    if column_name not in df.columns or df[column_name].dropna().empty:
        return "N/A"

    valid_series = df[df[column_name].astype(str).str.strip() != ""][column_name]
    if valid_series.empty:
        return "N/A"

    counts = valid_series.value_counts()
    if counts.empty:
        return "N/A"

    return f"{counts.index[0]} ({counts.iloc[0]}{suffix})"


def _get_era_str(df_sub):
    """Calculates min-max active years for a filtered subset."""
    if "Year" not in df_sub.columns:
        return "Unknown"

    years = pd.to_numeric(df_sub["Year"], errors="coerce").dropna()
    years = years[years > 0]
    if years.empty:
        return "Unknown"

    min_y, max_y = int(years.min()), int(years.max())
    return f"{min_y}" if min_y == max_y else f"{min_y}–{max_y}"


def _get_top_rated_str(df_sub):
    """Calculates max rating and count of songs achieving that max rating."""
    if "Rating" not in df_sub.columns:
        return "0★"

    ratings = pd.to_numeric(df_sub["Rating"], errors="coerce").dropna()
    ratings = ratings[ratings > 0]
    if ratings.empty:
        return "0★"

    max_r = ratings.max()
    top_cnt = (ratings == max_r).sum()
    return f"{max_r:.1f}★ ({top_cnt})"


# --- MAIN DASHBOARD RENDERER ---
def render_dashboard(
    df,
    sel_artist="Select Artist",
    sel_composer="Select Composer",
    sel_lyricist="Select Lyricist",
    sel_language="Select Language",
    sel_genre="Select Genre",
    sel_year="Select Year",
):
    """Renders a center-aligned Symphony Data Hub dashboard with increased font sizes."""

    # Responsive CSS with center justification & scaled font sizes (+2pt)
    st.markdown(
        """
        <style>
        /* Expander Header Title: Bold & 5X size (~5rem / 80px) */
        .db-header-title {
            font-size: 3.5rem !important;
            font-weight: 900 !important;
            text-align: center !important;
            margin-bottom: 10px !important;
            color: #1a202c !important;
            line-height: 1.1 !important;
        }

        .db-metric-mini {
            line-height: 1.25 !important;
            margin-bottom: 6px !important;
            text-align: center !important;
        }
        
        .db-label {
            font-size: 12px !important; /* Raised by 2pt (from 10px) */
            color: #707485 !important;
            text-transform: uppercase;
            margin: 0 !important;
            padding: 0 !important;
            font-weight: 700;
            text-align: center !important;
        }
        
        .db-value {
            font-size: 14.5px !important; /* Raised by 2pt (from 12.5px) */
            color: #1a1a1a !important;
            font-weight: 700;
            margin: 0 !important;
            padding: 0 !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center !important;
        }

        /* Flexible Cards (Centered & +2pt Font Size) */
        .filter-card-clean {
            background-color: #f0f4f8;
            border-radius: 6px;
            padding: 10px 12px;
            margin-bottom: 8px;
            color: #1c2d42;
            font-size: 14px !important; /* Raised by 2pt (from 12px) */
            line-height: 1.4;
            border-top: 4px solid #3182ce;
            text-align: center !important;
        }
        
        .filter-card-placeholder-clean {
            background-color: #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 8px;
            color: #718096;
            font-size: 14px !important; /* Raised by 2pt (from 12px) */
            font-weight: 600;
            text-align: center !important;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 72px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📊 Symphony Analytics Hub (Overall Stats & Filter Insights)", expanded=True):

        # 5X Large Center-Justified Bold Header
        st.markdown(
            '<div class="db-header-title">📊 Symphony Analytics Hub<br><span style="font-size: 2rem; font-weight: 700; color: #4a5568;">(Overall Stats & Filter Insights)</span></div>',
            unsafe_allow_html=True,
        )

        # --- OVERALL STATS SECTION ---
        with st.container(border=True):
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            with m1:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Singer</p><p class="db-value">{_get_top_stat(df, "Artist")}</p></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Composer</p><p class="db-value">{_get_top_stat(df, "Composer")}</p></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Lyricist</p><p class="db-value">{_get_top_stat(df, "Lyricist")}</p></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Album</p><p class="db-value">{_get_top_stat(df, "Album")}</p></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Genre</p><p class="db-value">{_get_top_stat(df, "Genre")}</p></div>', unsafe_allow_html=True)
            with m6:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Language</p><p class="db-value">{_get_top_stat(df, "Language")}</p></div>', unsafe_allow_html=True)
            with m7:
                st.markdown(f'<div class="db-metric-mini"><p class="db-label">Top Year</p><p class="db-value">{_get_top_stat(df, "Year")}</p></div>', unsafe_allow_html=True)

            if "Rating" in df.columns:
                ratings = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)
                st.markdown(
                    f"""
                    <div style="font-size: 13px; color: #4a5568; background-color: #f7fafc; padding: 6px 8px; border-radius: 4px; border: 1px solid #e2e8f0; text-align: center; margin-top: 6px;">
                        <b>Rating Breakdown:</b> 
                        5★: <b>{int((ratings >= 5).sum())}</b> &nbsp;|&nbsp; 
                        4★: <b>{int(((ratings >= 4) & (ratings < 5)).sum())}</b> &nbsp;|&nbsp; 
                        3★: <b>{int(((ratings >= 3) & (ratings < 4)).sum())}</b> &nbsp;|&nbsp; 
                        2★: <b>{int(((ratings >= 2) & (ratings < 3)).sum())}</b> &nbsp;|&nbsp; 
                        1★: <b>{int(((ratings > 0) & (ratings < 2)).sum())}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # --- FILTERED INSIGHTS GRID ---
        r1_c1, r1_c2, r1_c3 = st.columns(3)
        r2_c1, r2_c2, r2_c3 = st.columns(3)

        # 1. ARTIST INSIGHT CARD
        with r1_c1:
            if sel_artist and sel_artist != "Select Artist":
                art_mask = df["Artist"].astype(str).str.contains(sel_artist, case=False, na=False) | \
                           (df["Album Artist"].astype(str).str.contains(sel_artist, case=False, na=False) if "Album Artist" in df.columns else False)
                sub = df[art_mask]
                
                total = len(sub)
                solo = len(sub[sub["Album Artist"].isna() | (sub["Album Artist"].astype(str).str.strip() == "")]) if "Album Artist" in sub.columns else total
                group = total - solo
                era = _get_era_str(sub)
                top_rated = _get_top_rated_str(sub)
                
                comp = _split_and_top(sub["Composer"]) if "Composer" in sub.columns else "N/A"
                lyr = _split_and_top(sub["Lyricist"]) if "Lyricist" in sub.columns else "N/A"

                html_content = f"""
                <div class="filter-card-clean">
                    <b>{sel_artist} ({era})</b><br>
                    {total} songs ({solo} Solo, {group} Grp)<br>
                    <b>Top Rated:</b> {top_rated} | <b>Composer:</b> {comp}<br>
                    <b>Lyricist:</b> {lyr}
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown('<div class="filter-card-placeholder-clean">Select Artist</div>', unsafe_allow_html=True)

        # 2. COMPOSER INSIGHT CARD
        with r1_c2:
            if sel_composer and sel_composer != "Select Composer":
                sub = df[df["Composer"].astype(str).str.contains(sel_composer, case=False, na=False)]
                total = len(sub)
                era = _get_era_str(sub)
                top_rated = _get_top_rated_str(sub)

                singer = _split_and_top(sub["Artist"]) if "Artist" in sub.columns else "N/A"
                lyr = _split_and_top(sub["Lyricist"]) if "Lyricist" in sub.columns else "N/A"

                html_content = f"""
                <div class="filter-card-clean">
                    <b>{sel_composer} ({era})</b><br>
                    {total} songs<br>
                    <b>Top Rated:</b> {top_rated} | <b>Singer:</b> {singer}<br>
                    <b>Lyricist:</b> {lyr}
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown('<div class="filter-card-placeholder-clean">Select Composer</div>', unsafe_allow_html=True)

        # 3. LYRICIST INSIGHT CARD
        with r1_c3:
            if sel_lyricist and sel_lyricist != "Select Lyricist":
                sub = df[df["Lyricist"].astype(str).str.contains(sel_lyricist, case=False, na=False)]
                total = len(sub)
                era = _get_era_str(sub)
                top_rated = _get_top_rated_str(sub)

                singer = _split_and_top(sub["Artist"]) if "Artist" in sub.columns else "N/A"
                comp = _split_and_top(sub["Composer"]) if "Composer" in sub.columns else "N/A"

                html_content = f"""
                <div class="filter-card-clean">
                    <b>{sel_lyricist} ({era})</b><br>
                    {total} songs<br>
                    <b>Top Rated:</b> {top_rated} | <b>Singer:</b> {singer}<br>
                    <b>Composer:</b> {comp}
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown('<div class="filter-card-placeholder-clean">Select Lyricist</div>', unsafe_allow_html=True)

        # 4. LANGUAGE INSIGHT CARD
        with r2_c1:
            if sel_language and sel_language != "Select Language":
                sub = df[df["Language"].astype(str).str.strip().str.lower() == str(sel_language).strip().lower()]
                total = len(sub)

                singer = _split_and_top(sub["Artist"]) if "Artist" in sub.columns else "N/A"
                comp = _split_and_top(sub["Composer"]) if "Composer" in sub.columns else "N/A"

                html_content = f"""
                <div class="filter-card-clean">
                    <b>Language: {sel_language}</b><br>
                    <b>Total:</b> {total} songs<br>
                    <b>Top Singer:</b> {singer}<br>
                    <b>Top Composer:</b> {comp}
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown('<div class="filter-card-placeholder-clean">Select Language</div>', unsafe_allow_html=True)

        # 5. GENRE INSIGHT CARD
        with r2_c2:
            if sel_genre and sel_genre != "Select Genre":
                sub = df[df["Genre"].astype(str).str.contains(sel_genre, case=False, na=False)]
                total = len(sub)
                top_rated = _get_top_rated_str(sub)

                singer = _split_and_top(sub["Artist"]) if "Artist" in sub.columns else "N/A"
                comp = _split_and_top(sub["Composer"]) if "Composer" in sub.columns else "N/A"

                html_content = f"""
                <div class="filter-card-clean">
                    <b>Genre: {sel_genre}</b><br>
                    {total} songs<br>
                    <b>Top Rated:</b> {top_rated} | <b>Singer:</b> {singer}<br>
                    <b>Composer:</b> {comp}
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown('<div class="filter-card-placeholder-clean">Select Genre</div>', unsafe_allow_html=True)

        # 6. YEAR INSIGHT CARD
        with r2_c3:
            if sel_year and str(sel_year) != "Select Year":
                sub = df[pd.to_numeric(df["Year"], errors="coerce") == int(sel_year)]
                total = len(sub)
                top_rated = _get_top_rated_str(sub)

                singer = _split_and_top(sub["Artist"]) if "Artist" in sub.columns else "N/A"
                comp = _split_and_top(sub["Composer"]) if "Composer" in sub.columns else "N/A"

                html_content = f"""
                <div class="filter-card-clean">
                    <b>Year {sel_year}:</b> {total} songs<br>
                    <b>Top Rated:</b> {top_rated} | <b>Singer:</b> {singer}<br>
                    <b>Composer:</b> {comp}
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.markdown('<div class="filter-card-placeholder-clean">Select Year</div>', unsafe_allow_html=True)