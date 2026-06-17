# 🎯 Skill Gap Analyzer

A professional web application that helps users identify skill gaps between their current abilities and the requirements of their target job role, with personalized learning recommendations and analytics.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?logo=mysql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-38bdf8?logo=tailwindcss&logoColor=white)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Role Selection** | Choose from 12 curated tech job roles |
| **Skill Assessment** | Select your skills from 65+ categorized options |
| **Gap Analysis** | Set-based comparison of your skills vs role requirements |
| **Match Score** | Animated percentage showing your readiness |
| **Learning Paths** | Curated resources (courses, docs, tutorials) for missing skills |
| **Analytics Dashboard** | Charts & stats powered by Pandas + Matplotlib |
| **Dark Mode UI** | Premium glassmorphism design with TailwindCSS |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Analytics:** Pandas, Matplotlib
- **Frontend:** HTML, TailwindCSS (CDN), Custom CSS
- **Connector:** mysql-connector-python

---

## 📁 Project Structure

```
skill-gap-analyzer/
├── app.py                  # Flask application (routes + analysis engine)
├── config.py               # MySQL & Flask configuration
├── setup_db.py             # Database schema + seed data
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css       # Custom glassmorphism styles
│   └── charts/             # Matplotlib-generated chart images
├── templates/
│   ├── base.html           # Base layout (nav, footer)
│   ├── index.html          # Home — form with role & skill selection
│   ├── results.html        # Results — match %, skills, resources
│   └── analytics.html      # Dashboard — stats, charts, table
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** installed
- **MySQL 5.7+** installed and running

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/skill-gap-analyzer.git
cd skill-gap-analyzer
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL Password

Open `config.py` and set your MySQL root password:

```python
MYSQL_PASSWORD = 'your-mysql-password'
```

### 5. Set Up the Database

```bash
python setup_db.py
```

This creates the `skill_gap_analyzer` database with all tables and seed data.

### 6. Run the Application

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 📊 Database Schema

| Table | Purpose |
|---|---|
| `users` | Stores user profiles |
| `skills` | Master list of 65 technical skills |
| `user_skills` | Maps users to their current skills |
| `job_roles` | 12 target job roles with descriptions |
| `role_skills` | Required skills per role with importance levels |
| `learning_resources` | Curated learning links per skill |
| `analysis_history` | Stores every analysis result |

---

## 📸 Pages

1. **Home Page** — Enter name, select target role, check your skills
2. **Results Page** — Match percentage ring, matched/missing skills, learning recommendations
3. **Analytics Dashboard** — Stats cards, Matplotlib charts, recent analyses table

---

## 📝 License

This project is for educational purposes.