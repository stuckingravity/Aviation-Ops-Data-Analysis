import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ============================================================================
# TRANSLATIONS
# ============================================================================
TRANSLATIONS = {
    'en': {
        'title': '🛫 Airport Ground Operations Analysis',
        'subtitle': 'Task-Level Performance Dashboard | Tarmac Technologies',
        'sidebar_title': 'Filters',
        'airport_filter': 'Airport',
        'aircraft_filter': 'Aircraft Type',
        'task_filter': 'Task Type',
        'all': 'All',
        'clear_all': 'Clear All Filters',
        'kpi_section': 'Key Performance Indicators',
        'on_time_rate': 'On-Time Rate',
        'avg_delay': 'Average Delay',
        'total_tasks': 'Total Tasks',
        'unique_turnarounds': 'Unique Turnarounds',
        'delay_variability': 'Delay Variability (SD)',
        'task_distribution': 'Task Distribution',
        'delay_by_airport': 'Average Delay by Airport',
        'delay_by_aircraft': 'Average Delay by Aircraft Type',
        'delay_by_task': 'Top 10 Tasks by Delay',
        'delay_timeline': 'Delay Timeline',
        'delay_heatmap': 'Task Delay Heatmap',
        'punctuality_breakdown': 'Punctuality Breakdown',
        'on_time': 'On Time',
        'delayed': 'Delayed',
        'minutes': 'min',
        'tasks': 'tasks',
        'turnarounds': 'turnarounds',
        'detailed_data': 'Detailed Task Data',
        'download_csv': 'Download CSV',
        'airport_col': 'Airport',
        'aircraft_col': 'Aircraft',
        'task_col': 'Task',
        'delay_col': 'End Delay (min)',
        'duration_col': 'Duration (min)',
        'status_col': 'Status',
        'no_data': 'No data available for selected filters',
        'language': 'Language'
    },
    'fr': {
        'title': '🛫 Interface d\'analyse des opérations',
        'subtitle': 'Tableau de bord des performances par tâche | Tarmac Technologies',
        'sidebar_title': 'Filtres',
        'airport_filter': 'Aéroport',
        'aircraft_filter': 'Type d\'avion',
        'task_filter': 'Type de tâche',
        'all': 'Tous',
        'clear_all': 'Effacer tous les filtres',
        'kpi_section': 'Indicateurs clés de performance',
        'on_time_rate': 'Taux de ponctualité',
        'avg_delay': 'Retard moyen',
        'total_tasks': 'Nombre de tâches',
        'unique_turnarounds': 'Nombre de turnarounds distincts',
        'delay_variability': 'Variabilité ponctualité',
        'task_distribution': 'Répartition des tâches',
        'delay_by_airport': 'Retard moyen par aéroport',
        'delay_by_aircraft': 'Retard moyen par type d\'avion',
        'delay_by_task': 'Top 10 tâches par retard',
        'delay_timeline': 'Chronologie des retards',
        'delay_heatmap': 'Carte thermique des retards',
        'punctuality_breakdown': 'Répartition de la ponctualité',
        'on_time': 'À l\'heure',
        'delayed': 'En retard',
        'minutes': 'min',
        'tasks': 'tâches',
        'turnarounds': 'turnarounds',
        'detailed_data': 'Données détaillées des tâches',
        'download_csv': 'Télécharger CSV',
        'airport_col': 'Aéroport',
        'aircraft_col': 'Avion',
        'task_col': 'Tâche',
        'delay_col': 'Retard fin (min)',
        'duration_col': 'Durée (min)',
        'status_col': 'Statut',
        'no_data': 'Aucune donnée disponible pour les filtres sélectionnés',
        'language': 'Langue'
    }
}

# ============================================================================
# DATA LOADING & PROCESSING (Based on your notebook logic)
# ============================================================================

@st.cache_data
def load_and_process_data(filepath):
    """Load and clean data following the notebook logic"""
    
    # Load raw data
    df = pd.read_excel('Tarmac.xlsx', sheet_name='Data')
    
    # 1.1 Parse flight-level time fields
    for col in ['std', 'atd', 'sta', 'ata']:
        df[col + '_dt'] = pd.to_datetime(
            df[col].str.replace(' - ', ' ', regex=False), errors='coerce'
        )
    
    # 1.2 Parse task-level time fields + cross-midnight fix
    df['base_date'] = df['std_dt'].dt.date
    df['std_hour'] = df['std_dt'].dt.hour
    
    def parse_task_time(row, time_col):
        val, base, std_h = row[time_col], row['base_date'], row['std_hour']
        if pd.isna(val) or pd.isna(base):
            return pd.NaT
        try:
            t = pd.to_datetime(str(val).strip(), format='%H:%M').time()
            dt = pd.Timestamp.combine(base, t)
            if t.hour - std_h > 12:
                dt -= pd.Timedelta(days=1)
            elif std_h - t.hour > 12:
                dt += pd.Timedelta(days=1)
            return dt
        except:
            return pd.NaT
    
    for col in ['planning_start', 'actual_start', 'planning_end', 'actual_end']:
        df[col + '_dt'] = df.apply(lambda r: parse_task_time(r, col), axis=1)
    
    # 1.3 Build turnaround-level summary table
    ta = df.groupby('turnaround_id').agg(
        airport=('airport_iata_code', 'first'),
        aircraft=('aircraft', 'first'),
        std=('std_dt', 'first'),
        atd=('atd_dt', 'first'),
        sta=('sta_dt', 'first'),
        ata=('ata_dt', 'first'),
        adc=('adc', 'first'),
        adct=('adct', 'first'),
    ).reset_index()
    
    ta['dep_delay_min'] = (ta['atd'] - ta['std']).dt.total_seconds() / 60
    ta['adc_diff_min'] = (ta['adc'] - ta['adct']).dt.total_seconds() / 60
    ta['date'] = ta['std'].dt.date
    
    # 1.4 Build task-level table (deduplicate)
    tasks = df[['turnaround_id', 'airport_iata_code', 'aircraft', 'task_name',
                'planning_start_dt', 'actual_start_dt',
                'planning_end_dt', 'actual_end_dt']].drop_duplicates(
        subset=['turnaround_id', 'task_name']
    )
    
    tasks['end_delay_min'] = (tasks['actual_end_dt'] - tasks['planning_end_dt']).dt.total_seconds() / 60
    tasks['actual_duration_min'] = (tasks['actual_end_dt'] - tasks['actual_start_dt']).dt.total_seconds() / 60
    tasks['planned_duration_min'] = (tasks['planning_end_dt'] - tasks['planning_start_dt']).dt.total_seconds() / 60
    tasks['is_delayed'] = tasks['end_delay_min'] > 0
    
    # Validation: Fix ADC > ATD anomaly
    ta.loc[ta.adc.notna() & ta.atd.notna() & (ta.adc > ta.atd), 'adc'] = pd.NaT
    ta.loc[ta.adc.isna(), 'adc_diff_min'] = np.nan
    
    # Add date to tasks for timeline analysis
    tasks = tasks.merge(ta[['turnaround_id', 'date']], on='turnaround_id', how='left')
    
    return tasks, ta


# ============================================================================
# UI COMPONENTS
# ============================================================================

def create_kpi_card(label, value, icon="📊", color="#2563eb", lang='en'):
    """Create a modern KPI card"""
    t = TRANSLATIONS[lang]
    
    # Format value based on type
    if isinstance(value, float):
        if 'rate' in label.lower() or '%' in str(value):
            display_value = f"{value:.1f}%"
        else:
            display_value = f"{value:.1f} {t['minutes']}"
    else:
        display_value = f"{value:,}"
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <span style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                {label}
            </span>
        </div>
        <div style="font-size: 1.75rem; font-weight: 700; color: {color};">
            {display_value}
        </div>
    </div>
    """, unsafe_allow_html=True)


def calculate_kpis(filtered_tasks, lang='en'):
    """Calculate KPIs from filtered tasks"""
    t = TRANSLATIONS[lang]
    
    if filtered_tasks.empty:
        return {
            'on_time_rate': 0,
            'avg_delay': 0,
            'total_tasks': 0,
            'unique_turnarounds': 0,
            'delay_variability': 0
        }
    
    # On-time rate: tasks completed on or before planned end time
    on_time_count = (filtered_tasks['end_delay_min'] <= 0).sum()
    on_time_rate = (on_time_count / len(filtered_tasks)) * 100
    
    # Average delay (only delayed tasks)
    delayed_tasks = filtered_tasks[filtered_tasks['end_delay_min'] > 0]
    avg_delay = delayed_tasks['end_delay_min'].mean() if not delayed_tasks.empty else 0
    
    # Delay variability (standard deviation)
    delay_variability = filtered_tasks['end_delay_min'].std() if len(filtered_tasks) > 1 else 0
    
    return {
        'on_time_rate': on_time_rate,
        'avg_delay': avg_delay,
        'total_tasks': len(filtered_tasks),
        'unique_turnarounds': filtered_tasks['turnaround_id'].nunique(),
        'delay_variability': delay_variability
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_task_distribution_chart(filtered_tasks, lang='en'):
    """Create task distribution pie chart"""
    t = TRANSLATIONS[lang]
    
    task_counts = filtered_tasks['task_name'].value_counts().reset_index()
    task_counts.columns = ['task_name', 'count']
    
    fig = px.pie(
        task_counts,
        values='count',
        names='task_name',
        title=t['task_distribution'],
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        showlegend=False,
        height=400,
        font=dict(size=11)
    )
    
    return fig


def create_delay_by_airport(filtered_tasks, lang='en'):
    """Create delay breakdown by airport"""
    t = TRANSLATIONS[lang]
    
    airport_delay = filtered_tasks.groupby('airport_iata_code').agg(
        avg_delay=('end_delay_min', 'mean'),
        count=('task_name', 'count')
    ).reset_index().sort_values('avg_delay', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=airport_delay['airport_iata_code'],
        x=airport_delay['avg_delay'],
        orientation='h',
        marker=dict(
            color=airport_delay['avg_delay'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title=t['minutes'])
        ),
        text=[f"{x:.1f} {t['minutes']}" for x in airport_delay['avg_delay']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' + t['avg_delay'] + ': %{x:.1f} ' + t['minutes'] + '<br>' + 
                      t['tasks'] + ': %{customdata}<extra></extra>',
        customdata=airport_delay['count']
    ))
    
    fig.update_layout(
        title=t['delay_by_airport'],
        xaxis_title=t['avg_delay'] + ' (' + t['minutes'] + ')',
        yaxis_title=t['airport_col'],
        height=300,
        margin=dict(l=10, r=10, t=40, b=40)
    )
    
    return fig


def create_delay_by_aircraft(filtered_tasks, lang='en'):
    """Create delay breakdown by aircraft type"""
    t = TRANSLATIONS[lang]
    
    aircraft_delay = filtered_tasks.groupby('aircraft').agg(
        avg_delay=('end_delay_min', 'mean'),
        count=('task_name', 'count')
    ).reset_index().sort_values('avg_delay', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=aircraft_delay['aircraft'],
        x=aircraft_delay['avg_delay'],
        orientation='h',
        marker=dict(
            color=aircraft_delay['avg_delay'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=t['minutes'])
        ),
        text=[f"{x:.1f} {t['minutes']}" for x in aircraft_delay['avg_delay']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' + t['avg_delay'] + ': %{x:.1f} ' + t['minutes'] + '<br>' + 
                      t['tasks'] + ': %{customdata}<extra></extra>',
        customdata=aircraft_delay['count']
    ))
    
    fig.update_layout(
        title=t['delay_by_aircraft'],
        xaxis_title=t['avg_delay'] + ' (' + t['minutes'] + ')',
        yaxis_title=t['aircraft_col'],
        height=250,
        margin=dict(l=10, r=10, t=40, b=40)
    )
    
    return fig


def create_delay_by_task(filtered_tasks, lang='en'):
    """Create top 10 delayed tasks chart"""
    t = TRANSLATIONS[lang]
    
    task_delay = filtered_tasks.groupby('task_name').agg(
        avg_delay=('end_delay_min', 'mean'),
        count=('task_name', 'count')
    ).reset_index().sort_values('avg_delay', ascending=False).head(10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=task_delay['task_name'],
        y=task_delay['avg_delay'],
        marker=dict(
            color=task_delay['avg_delay'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title=t['minutes'])
        ),
        text=[f"{x:.1f}" for x in task_delay['avg_delay']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' + t['avg_delay'] + ': %{y:.1f} ' + t['minutes'] + '<br>' + 
                      t['tasks'] + ': %{customdata}<extra></extra>',
        customdata=task_delay['count']
    ))
    
    fig.update_layout(
        title=t['delay_by_task'],
        xaxis_title=t['task_col'],
        yaxis_title=t['avg_delay'] + ' (' + t['minutes'] + ')',
        height=400,
        xaxis_tickangle=-45,
        margin=dict(l=10, r=10, t=40, b=100)
    )
    
    return fig


def create_delay_timeline(filtered_tasks, lang='en'):
    """Create delay timeline by date"""
    t = TRANSLATIONS[lang]
    
    # Group by date
    daily_delay = filtered_tasks.groupby('date').agg(
        avg_delay=('end_delay_min', 'mean'),
        count=('task_name', 'count')
    ).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_delay['date'],
        y=daily_delay['avg_delay'],
        mode='lines+markers',
        line=dict(color='#2563eb', width=2),
        marker=dict(size=8, color='#2563eb'),
        fill='tozeroy',
        fillcolor='rgba(37, 99, 235, 0.1)',
        hovertemplate='<b>%{x}</b><br>' + t['avg_delay'] + ': %{y:.1f} ' + t['minutes'] + 
                      '<br>' + t['tasks'] + ': %{customdata}<extra></extra>',
        customdata=daily_delay['count']
    ))
    
    fig.update_layout(
        title=t['delay_timeline'],
        xaxis_title='Date',
        yaxis_title=t['avg_delay'] + ' (' + t['minutes'] + ')',
        height=350,
        margin=dict(l=10, r=10, t=40, b=40),
        hovermode='x unified'
    )
    
    return fig


def create_delay_heatmap(filtered_tasks, lang='en'):
    """Create heatmap of delays by airport and task"""
    t = TRANSLATIONS[lang]
    
    # Pivot table
    pivot = filtered_tasks.pivot_table(
        values='end_delay_min',
        index='task_name',
        columns='airport_iata_code',
        aggfunc='mean'
    ).fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn_r',
        colorbar=dict(title=t['minutes']),
        hovertemplate=t['airport_col'] + ': %{x}<br>' + 
                      t['task_col'] + ': %{y}<br>' + 
                      t['avg_delay'] + ': %{z:.1f} ' + t['minutes'] + '<extra></extra>'
    ))
    
    fig.update_layout(
        title=t['delay_heatmap'],
        xaxis_title=t['airport_col'],
        yaxis_title=t['task_col'],
        height=max(400, len(pivot.index) * 20),
        margin=dict(l=150, r=10, t=40, b=40)
    )
    
    return fig


def create_punctuality_breakdown(filtered_tasks, lang='en'):
    """Create punctuality breakdown chart"""
    t = TRANSLATIONS[lang]
    
    punctuality = filtered_tasks.groupby('is_delayed').size().reset_index(name='count')
    punctuality['status'] = punctuality['is_delayed'].map({False: t['on_time'], True: t['delayed']})
    
    fig = go.Figure(data=[go.Pie(
        labels=punctuality['status'],
        values=punctuality['count'],
        marker=dict(colors=['#16a34a', '#dc2626']),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>' + t['tasks'] + ': %{value}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=t['punctuality_breakdown'],
        height=350,
        showlegend=True,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Page config
    st.set_page_config(
        page_title="Turnaround Analysis | Tarmac",
        page_icon="🛫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stMetric { background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; }
    div[data-testid="stSidebar"] { background: #f8fafc; }
    .stMultiSelect [data-baseweb="tag"] { background-color: #dc2626; }
    h1 { font-size: 1.75rem !important; margin-bottom: 0.25rem !important; }
    h2 { font-size: 1.25rem !important; margin-top: 1.5rem !important; }
    h3 { font-size: 1rem !important; margin-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)
    
    # Load data
    try:
        tasks, ta = load_and_process_data('Tarmac.xlsx')
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return
    
    # ========================================================================
    # SIDEBAR - Language & Filters
    # ========================================================================
    
    with st.sidebar:
        # Language selector at top
        lang = st.selectbox(
            "🌐 Language / Langue",
            options=['en', 'fr'],
            format_func=lambda x: 'English' if x == 'en' else 'Français',
            index=1  # Default to French
        )
        
        t = TRANSLATIONS[lang]
        
        st.markdown(f"### {t['sidebar_title']}")
        st.markdown("---")
        
        # Airport filter
        airports = ['All'] + sorted(tasks['airport_iata_code'].dropna().unique().tolist())
        selected_airports = st.multiselect(
            t['airport_filter'],
            options=airports[1:],  # Exclude 'All' from options
            default=[]
        )
        
        # Aircraft filter
        aircraft_types = ['All'] + sorted(tasks['aircraft'].dropna().unique().tolist())
        selected_aircraft = st.multiselect(
            t['aircraft_filter'],
            options=aircraft_types[1:],
            default=[]
        )
        
        # Task type filter
        task_types = ['All'] + sorted(tasks['task_name'].dropna().unique().tolist())
        selected_tasks = st.multiselect(
            t['task_filter'],
            options=task_types[1:],
            default=[]
        )
        
        # Clear all button
        if st.button(t['clear_all'], use_container_width=True):
            st.rerun()
        
        # Filter info
        st.markdown("---")
        st.caption(f"📊 **{len(tasks):,}** {t['tasks']}")
        st.caption(f"✈️ **{tasks['turnaround_id'].nunique():,}** {t['turnarounds']}")
        st.caption(f"🏢 **{tasks['airport_iata_code'].nunique():,}** airports")
        st.caption(f"🛩️ **{tasks['aircraft'].nunique():,}** aircraft types")
    
    # ========================================================================
    # MAIN CONTENT
    # ========================================================================
    
    # Header
    st.markdown(f"# {t['title']}")
    st.markdown(f"<p style='color: #64748b; font-size: 0.9rem;'>{t['subtitle']}</p>", 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # Apply filters
    filtered_tasks = tasks.copy()
    
    if selected_airports:
        filtered_tasks = filtered_tasks[filtered_tasks['airport_iata_code'].isin(selected_airports)]
    
    if selected_aircraft:
        filtered_tasks = filtered_tasks[filtered_tasks['aircraft'].isin(selected_aircraft)]
    
    if selected_tasks:
        filtered_tasks = filtered_tasks[filtered_tasks['task_name'].isin(selected_tasks)]
    
    # Check if data exists
    if filtered_tasks.empty:
        st.warning(t['no_data'])
        return
    
    # ========================================================================
    # KPI CARDS
    # ========================================================================
    
    kpis = calculate_kpis(filtered_tasks, lang)
    
    st.markdown(f"## {t['kpi_section']}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        create_kpi_card(t['on_time_rate'], kpis['on_time_rate'], "✅", "#16a34a", lang)
    
    with col2:
        create_kpi_card(t['avg_delay'], kpis['avg_delay'], "⏱️", "#dc2626", lang)
    
    with col3:
        create_kpi_card(t['total_tasks'], kpis['total_tasks'], "📋", "#2563eb", lang)
    
    with col4:
        create_kpi_card(t['unique_turnarounds'], kpis['unique_turnarounds'], "🔄", "#0891b2", lang)
    
    with col5:
        create_kpi_card(t['delay_variability'], kpis['delay_variability'], "📊", "#ea580c", lang)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================================================
    # VISUALIZATIONS
    # ========================================================================
    
    # Row 1: Task distribution and punctuality
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.plotly_chart(create_task_distribution_chart(filtered_tasks, lang), 
                       use_container_width=True)
    
    with col2:
        st.plotly_chart(create_punctuality_breakdown(filtered_tasks, lang), 
                       use_container_width=True)
    
    # Row 2: Delay timeline
    st.plotly_chart(create_delay_timeline(filtered_tasks, lang), 
                   use_container_width=True)
    
    # Row 3: Delay by airport and aircraft
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.plotly_chart(create_delay_by_airport(filtered_tasks, lang), 
                       use_container_width=True)
    
    with col2:
        st.plotly_chart(create_delay_by_aircraft(filtered_tasks, lang), 
                       use_container_width=True)
    
    # Row 4: Top delayed tasks
    st.plotly_chart(create_delay_by_task(filtered_tasks, lang), 
                   use_container_width=True)
    
    # Row 5: Heatmap
    if len(filtered_tasks['airport_iata_code'].unique()) > 1 and len(filtered_tasks['task_name'].unique()) > 1:
        st.plotly_chart(create_delay_heatmap(filtered_tasks, lang), 
                       use_container_width=True)
    
    # ========================================================================
    # DETAILED DATA TABLE
    # ========================================================================
    
    st.markdown(f"## {t['detailed_data']}")
    
    # Prepare display dataframe
    display_df = filtered_tasks[[
        'airport_iata_code', 'aircraft', 'task_name', 
        'end_delay_min', 'actual_duration_min', 'is_delayed'
    ]].copy()
    
    display_df.columns = [
        t['airport_col'], 
        t['aircraft_col'], 
        t['task_col'], 
        t['delay_col'], 
        t['duration_col'], 
        t['status_col']
    ]
    
    display_df[t['status_col']] = display_df[t['status_col']].map({
        False: t['on_time'], 
        True: t['delayed']
    })
    
    # Round numeric columns
    display_df[t['delay_col']] = display_df[t['delay_col']].round(1)
    display_df[t['duration_col']] = display_df[t['duration_col']].round(1)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Download button
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 {t['download_csv']}",
        data=csv,
        file_name=f"turnaround_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
