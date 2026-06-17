"""
Skill Gap Analyzer — Flask Application
=======================================
Main application file with routes, analysis engine,
and chart generation.

Run: python app.py
"""

import os
import json

import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (must be set before importing pyplot)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd

from config import Config

# ─── Flask App Setup ─────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)


# ─── Database Helper ─────────────────────────────────────────────
def get_db():
    """Return a new MySQL connection."""
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
    )


# ═══════════════════════════════════════════════════════════════════
# ROUTE 1 — HOME PAGE  (GET /)
# ═══════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    """Render the home page with role selector and skill checkboxes."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Fetch all job roles sorted by name
    cursor.execute("SELECT * FROM job_roles ORDER BY role_name")
    roles = cursor.fetchall()

    # Fetch all skills sorted by category then name
    cursor.execute("SELECT * FROM skills ORDER BY category, skill_name")
    skills = cursor.fetchall()

    # Group skills by category for display
    skills_by_category = {}
    for skill in skills:
        cat = skill['category']
        if cat not in skills_by_category:
            skills_by_category[cat] = []
        skills_by_category[cat].append(skill)

    # Define a nice order for categories
    category_order = [
        'Programming', 'Frontend', 'Backend', 'Database',
        'DevOps', 'Cloud', 'Data Science', 'Mobile',
        'Architecture', 'Methodology', 'Computer Science', 'Security'
    ]
    ordered_categories = []
    for cat in category_order:
        if cat in skills_by_category:
            ordered_categories.append((cat, skills_by_category[cat]))

    cursor.close()
    db.close()

    return render_template('index.html', roles=roles, ordered_categories=ordered_categories)


# ═══════════════════════════════════════════════════════════════════
# ROUTE 2 — ANALYZE  (POST /analyze)
# Skill Gap Analysis Engine
# ═══════════════════════════════════════════════════════════════════
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Core analysis engine:
    1. Receive form data (user name, role, selected skills)
    2. Insert/find user in database
    3. Store user's selected skills
    4. Fetch required skills for the chosen role
    5. Compare using set operations (intersection & difference)
    6. Calculate match percentage
    7. Store results in analysis_history
    8. Redirect to results page
    """
    # ── Collect form data ──
    user_name = request.form.get('user_name', '').strip()
    role_id = request.form.get('role_id')
    selected_skill_ids = request.form.getlist('skills')

    # ── Validate ──
    if not user_name:
        flash('Please enter your name.', 'error')
        return redirect(url_for('index'))
    if not role_id:
        flash('Please select a job role.', 'error')
        return redirect(url_for('index'))
    if not selected_skill_ids:
        flash('Please select at least one skill.', 'error')
        return redirect(url_for('index'))

    role_id = int(role_id)
    selected_skill_ids = [int(sid) for sid in selected_skill_ids]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # ── Step 1: Insert or find user ──
        cursor.execute("SELECT user_id FROM users WHERE name = %s", (user_name,))
        user = cursor.fetchone()

        if user:
            user_id = user['user_id']
            # Clear old skill selections for this user
            cursor.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (user_name,))
            user_id = cursor.lastrowid

        # ── Step 2: Store user's current skills ──
        for skill_id in selected_skill_ids:
            cursor.execute(
                "INSERT IGNORE INTO user_skills (user_id, skill_id) VALUES (%s, %s)",
                (user_id, skill_id)
            )

        # ── Step 3: Fetch required skills for the selected role ──
        cursor.execute("""
            SELECT s.skill_id, s.skill_name, s.category, rs.importance_level
            FROM role_skills rs
            JOIN skills s ON rs.skill_id = s.skill_id
            WHERE rs.role_id = %s
            ORDER BY FIELD(rs.importance_level, 'Critical', 'Important', 'Nice to Have'), s.skill_name
        """, (role_id,))
        required_skills = cursor.fetchall()

        # ── Step 4 & 5: Set comparison — matched vs missing ──
        required_skill_ids = {s['skill_id'] for s in required_skills}  # Set of required
        user_skill_set = set(selected_skill_ids)                       # Set of user's skills

        matched_ids = required_skill_ids & user_skill_set   # Intersection
        missing_ids = required_skill_ids - user_skill_set   # Difference

        matched_skills = [s for s in required_skills if s['skill_id'] in matched_ids]
        missing_skills = [s for s in required_skills if s['skill_id'] in missing_ids]

        # ── Step 6: Calculate match percentage ──
        if len(required_skill_ids) > 0:
            match_percentage = round(len(matched_ids) / len(required_skill_ids) * 100, 1)
        else:
            match_percentage = 0.0

        # ── Step 7: Store result in analysis_history ──
        cursor.execute("""
            INSERT INTO analysis_history
                (user_id, role_id, match_percentage, matched_skills, missing_skills)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            role_id,
            match_percentage,
            json.dumps([s['skill_name'] for s in matched_skills]),
            json.dumps([s['skill_name'] for s in missing_skills]),
        ))
        analysis_id = cursor.lastrowid

        db.commit()

    except Exception as e:
        db.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

    finally:
        cursor.close()
        db.close()

    # ── Step 8: Redirect to results page ──
    return redirect(url_for('results', analysis_id=analysis_id))


# ═══════════════════════════════════════════════════════════════════
# ROUTE 3 — RESULTS PAGE  (GET /results/<id>)
# ═══════════════════════════════════════════════════════════════════
@app.route('/results/<int:analysis_id>')
def results(analysis_id):
    """Display analysis results with matched/missing skills and learning resources."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Fetch analysis with user and role info (INNER JOIN)
    cursor.execute("""
        SELECT ah.*, u.name AS user_name, jr.role_name, jr.description AS role_description
        FROM analysis_history ah
        INNER JOIN users u ON ah.user_id = u.user_id
        INNER JOIN job_roles jr ON ah.role_id = jr.role_id
        WHERE ah.analysis_id = %s
    """, (analysis_id,))
    analysis = cursor.fetchone()

    if not analysis:
        flash('Analysis not found.', 'error')
        cursor.close()
        db.close()
        return redirect(url_for('index'))

    matched_skills = json.loads(analysis['matched_skills'])
    missing_skills = json.loads(analysis['missing_skills'])

    # Fetch learning resources for missing skills (LEFT JOIN ensures all missing skills appear)
    resources_by_skill = {}
    if missing_skills:
        placeholders = ', '.join(['%s'] * len(missing_skills))
        query = """
            SELECT lr.title, lr.url, lr.platform, lr.resource_type, s.skill_name
            FROM skills s
            LEFT JOIN learning_resources lr ON s.skill_id = lr.skill_id
            WHERE s.skill_name IN ({})
            ORDER BY s.skill_name, lr.platform
        """.format(placeholders)
        cursor.execute(query, missing_skills)
        rows = cursor.fetchall()
        for row in rows:
            skill = row['skill_name']
            if skill not in resources_by_skill:
                resources_by_skill[skill] = []
            if row['title']:  # Only add if resource exists (LEFT JOIN may give NULL)
                resources_by_skill[skill].append(row)

    cursor.close()
    db.close()

    return render_template(
        'results.html',
        analysis=analysis,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        resources_by_skill=resources_by_skill,
        match_percentage=float(analysis['match_percentage']),
    )


# ═══════════════════════════════════════════════════════════════════
# ROUTE 4 — ANALYTICS DASHBOARD  (GET /analytics)
# ═══════════════════════════════════════════════════════════════════
@app.route('/analytics')
def analytics():
    """
    Generate analytics using SQL + Pandas.
    Create Matplotlib charts and save them as images.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # ── Check if we have any data ──
    cursor.execute("SELECT COUNT(*) AS total FROM analysis_history")
    total_analyses = cursor.fetchone()['total']

    if total_analyses == 0:
        cursor.close()
        db.close()
        return render_template('analytics.html', has_data=False)

    # ── Load analysis history into a Pandas DataFrame ──
    cursor.execute("""
        SELECT ah.analysis_id, ah.match_percentage, ah.matched_skills,
               ah.missing_skills, ah.analyzed_at,
               u.name AS user_name, jr.role_name
        FROM analysis_history ah
        INNER JOIN users u ON ah.user_id = u.user_id
        INNER JOIN job_roles jr ON ah.role_id = jr.role_id
        ORDER BY ah.analyzed_at DESC
    """)
    history = cursor.fetchall()
    df = pd.DataFrame(history)

    # ── Metric 1: Total Analyses (already have it) ──

    # ── Metric 2: Average Match Percentage (Pandas aggregation) ──
    avg_match = round(df['match_percentage'].astype(float).mean(), 1)

    # ── Metric 3: Most Selected Role (Pandas mode / groupby) ──
    role_counts = df.groupby('role_name').size().reset_index(name='count')
    role_counts = role_counts.sort_values('count', ascending=False)
    most_selected_role = role_counts.iloc[0]['role_name']
    most_selected_role_count = int(role_counts.iloc[0]['count'])

    # ── Metric 4: Most Demanded Skill (SQL aggregate) ──
    cursor.execute("""
        SELECT s.skill_name, COUNT(*) AS demand_count
        FROM role_skills rs
        INNER JOIN skills s ON rs.skill_id = s.skill_id
        GROUP BY s.skill_name
        ORDER BY demand_count DESC
        LIMIT 1
    """)
    most_demanded = cursor.fetchone()

    # ── Metric 5 & 6: Most Missing Skill (Pandas Series) ──
    all_missing = []
    for ms_json in df['missing_skills']:
        parsed = json.loads(ms_json) if isinstance(ms_json, str) else ms_json
        all_missing.extend(parsed)

    if all_missing:
        missing_series = pd.Series(all_missing)
        missing_value_counts = missing_series.value_counts()
        most_missing_skill = missing_value_counts.index[0]
        most_missing_count = int(missing_value_counts.iloc[0])
    else:
        most_missing_skill = 'N/A'
        most_missing_count = 0

    # ── Metric 7: Recent analyses (latest 10) ──
    recent_df = df.head(10)[['user_name', 'role_name', 'match_percentage', 'analyzed_at']]
    recent_analyses = recent_df.to_dict('records')

    # ═══════════════════════════════════════════════
    # CHART GENERATION (Matplotlib)
    # ═══════════════════════════════════════════════
    chart_dir = os.path.join(app.static_folder, 'charts')
    os.makedirs(chart_dir, exist_ok=True)
    charts = {}

    # Common chart styling
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
    })

    # ── Chart 1: Match Percentage Pie Chart ──
    try:
        percentages = df['match_percentage'].astype(float).tolist()
        ranges = {'0–25%': 0, '26–50%': 0, '51–75%': 0, '76–100%': 0}
        for p in percentages:
            if p <= 25:
                ranges['0–25%'] += 1
            elif p <= 50:
                ranges['26–50%'] += 1
            elif p <= 75:
                ranges['51–75%'] += 1
            else:
                ranges['76–100%'] += 1

        non_zero = {k: v for k, v in ranges.items() if v > 0}
        if non_zero:
            fig, ax = plt.subplots(figsize=(7, 5), facecolor='#0f172a')
            ax.set_facecolor('#0f172a')
            colors_map = {'0–25%': '#ef4444', '26–50%': '#f59e0b', '51–75%': '#3b82f6', '76–100%': '#10b981'}
            chart_colors = [colors_map[k] for k in non_zero]
            wedges, texts, autotexts = ax.pie(
                non_zero.values(), labels=non_zero.keys(),
                autopct='%1.1f%%', colors=chart_colors,
                textprops={'color': 'white', 'fontsize': 11},
                wedgeprops={'edgecolor': '#1e293b', 'linewidth': 2},
                startangle=90,
            )
            for t in autotexts:
                t.set_fontweight('bold')
            ax.set_title('Match Percentage Distribution', color='white', pad=15)
            plt.tight_layout()
            path = os.path.join(chart_dir, 'match_distribution.png')
            plt.savefig(path, facecolor='#0f172a', dpi=120, bbox_inches='tight')
            plt.close()
            charts['match_distribution'] = 'charts/match_distribution.png'
    except Exception as e:
        print(f'Chart error: {e}')
        plt.close('all')

    # ── Chart 2: Most Missing Skills Bar Chart ──
    try:
        if all_missing:
            top_missing = missing_value_counts.head(10)
            fig, ax = plt.subplots(figsize=(9, 5), facecolor='#0f172a')
            ax.set_facecolor('#1e293b')
            bars = ax.barh(
                top_missing.index[::-1], top_missing.values[::-1],
                color='#f43f5e', edgecolor='#fb7185', linewidth=0.5,
                height=0.6
            )
            ax.set_xlabel('Times Missing', color='white', fontsize=12)
            ax.set_title('Top Missing Skills', color='white', pad=15)
            ax.tick_params(colors='white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#475569')
            ax.spines['left'].set_color('#475569')
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                        f'{int(width)}', ha='left', va='center', color='white', fontsize=10)
            plt.tight_layout()
            path = os.path.join(chart_dir, 'missing_skills.png')
            plt.savefig(path, facecolor='#0f172a', dpi=120, bbox_inches='tight')
            plt.close()
            charts['missing_skills'] = 'charts/missing_skills.png'
    except Exception as e:
        print(f'Chart error: {e}')
        plt.close('all')
    try:
        cursor.execute("""
            SELECT s.skill_name, COUNT(*) AS demand
            FROM role_skills rs
            INNER JOIN skills s ON rs.skill_id = s.skill_id
            GROUP BY s.skill_name
            ORDER BY demand DESC
            LIMIT 10
        """)
        demand_data = cursor.fetchall()
        if demand_data:
            demand_df = pd.DataFrame(demand_data)
            fig, ax = plt.subplots(figsize=(9, 5), facecolor='#0f172a')
            ax.set_facecolor('#1e293b')
            bars = ax.barh(
                demand_df['skill_name'][::-1], demand_df['demand'][::-1],
                color='#6366f1', edgecolor='#818cf8', linewidth=0.5,
                height=0.6
            )
            ax.set_xlabel('Number of Roles Requiring Skill', color='white', fontsize=12)
            ax.set_title('Skill Demand Across All Roles', color='white', pad=15)
            ax.tick_params(colors='white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#475569')
            ax.spines['left'].set_color('#475569')
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                        f'{int(width)}', ha='left', va='center', color='white', fontsize=10)
            plt.tight_layout()
            path = os.path.join(chart_dir, 'skill_demand.png')
            plt.savefig(path, facecolor='#0f172a', dpi=120, bbox_inches='tight')
            plt.close()
            charts['skill_demand'] = 'charts/skill_demand.png'
    except Exception as e:
        print(f'Chart error: {e}')
        plt.close('all')
    try:
        if len(role_counts) > 0:
            fig, ax = plt.subplots(figsize=(9, 5), facecolor='#0f172a')
            ax.set_facecolor('#1e293b')
            gradient_colors = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe',
                               '#818cf8', '#7c3aed', '#5b21b6', '#4c1d95', '#3730a3',
                               '#6366f1', '#8b5cf6']
            bar_colors = gradient_colors[:len(role_counts)]
            ax.bar(
                role_counts['role_name'], role_counts['count'],
                color=bar_colors, edgecolor='#818cf8', linewidth=0.5, width=0.6
            )
            ax.set_ylabel('Number of Analyses', color='white', fontsize=12)
            ax.set_title('Job Role Popularity', color='white', pad=15)
            ax.tick_params(colors='white')
            plt.xticks(rotation=45, ha='right', fontsize=9)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#475569')
            ax.spines['left'].set_color('#475569')
            plt.tight_layout()
            path = os.path.join(chart_dir, 'role_popularity.png')
            plt.savefig(path, facecolor='#0f172a', dpi=120, bbox_inches='tight')
            plt.close()
            charts['role_popularity'] = 'charts/role_popularity.png'
    except Exception as e:
        print(f'Chart error: {e}')
        plt.close('all')

    cursor.close()
    db.close()

    return render_template(
        'analytics.html',
        has_data=True,
        total_analyses=total_analyses,
        avg_match=avg_match,
        most_selected_role=most_selected_role,
        most_selected_role_count=most_selected_role_count,
        most_demanded=most_demanded,
        most_missing_skill=most_missing_skill,
        most_missing_count=most_missing_count,
        charts=charts,
        recent_analyses=recent_analyses,
    )


# ═══════════════════════════════════════════════════════════════════
# APP ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)
