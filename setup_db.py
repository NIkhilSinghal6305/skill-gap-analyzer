"""
Database Setup Script for Skill Gap Analyzer
=============================================
Run this script ONCE to create the database, tables, and seed data.

Usage:
    python setup_db.py

Make sure MySQL is running and update config.py with your MySQL password first.
"""

import mysql.connector
from config import Config


def get_connection(use_database=False):
    """Create a MySQL connection."""
    params = {
        'host': Config.MYSQL_HOST,
        'user': Config.MYSQL_USER,
        'password': Config.MYSQL_PASSWORD,
    }
    if use_database:
        params['database'] = Config.MYSQL_DATABASE
    return mysql.connector.connect(**params)


def create_database(cursor):
    """Create the skill_gap_analyzer database."""
    print("Creating database...")
    cursor.execute(f"DROP DATABASE IF EXISTS {Config.MYSQL_DATABASE}")
    cursor.execute(f"CREATE DATABASE {Config.MYSQL_DATABASE}")
    cursor.execute(f"USE {Config.MYSQL_DATABASE}")
    print("  ✓ Database created successfully!")


def create_tables(cursor):
    """Create all tables with proper relationships and constraints."""
    print("\nCreating tables...")

    # ──────────────────────────────────────────────
    # TABLE 1: users
    # Stores registered user information.
    # Primary Key: user_id (auto-increment)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100) NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ users table created")

    # ──────────────────────────────────────────────
    # TABLE 2: skills
    # Master list of all technical skills.
    # Primary Key: skill_id (auto-increment)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            skill_id    INT AUTO_INCREMENT PRIMARY KEY,
            skill_name  VARCHAR(100) NOT NULL UNIQUE,
            category    VARCHAR(50) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ skills table created")

    # ──────────────────────────────────────────────
    # TABLE 3: user_skills
    # Junction table: links users to their skills.
    # Foreign Keys: user_id → users, skill_id → skills
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_skills (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id     INT NOT NULL,
            skill_id    INT NOT NULL,
            FOREIGN KEY (user_id)  REFERENCES users(user_id)  ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_skill (user_id, skill_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ user_skills table created")

    # ──────────────────────────────────────────────
    # TABLE 4: job_roles
    # All target job roles a user can select.
    # Primary Key: role_id (auto-increment)
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_roles (
            role_id     INT AUTO_INCREMENT PRIMARY KEY,
            role_name   VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            category    VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ job_roles table created")

    # ──────────────────────────────────────────────
    # TABLE 5: role_skills
    # Junction table: maps required skills per job role.
    # Foreign Keys: role_id → job_roles, skill_id → skills
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_skills (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            role_id           INT NOT NULL,
            skill_id          INT NOT NULL,
            importance_level  ENUM('Critical', 'Important', 'Nice to Have') DEFAULT 'Important',
            FOREIGN KEY (role_id)  REFERENCES job_roles(role_id)  ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
            UNIQUE KEY unique_role_skill (role_id, skill_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ role_skills table created")

    # ──────────────────────────────────────────────
    # TABLE 6: learning_resources
    # Curated learning links per skill.
    # Foreign Key: skill_id → skills
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_resources (
            resource_id   INT AUTO_INCREMENT PRIMARY KEY,
            skill_id      INT NOT NULL,
            title         VARCHAR(200) NOT NULL,
            url           VARCHAR(500),
            platform      VARCHAR(100),
            resource_type ENUM('Course', 'Documentation', 'Tutorial', 'Video', 'Book') DEFAULT 'Course',
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ learning_resources table created")

    # ──────────────────────────────────────────────
    # TABLE 7: analysis_history
    # Stores every analysis a user performs.
    # Foreign Keys: user_id → users, role_id → job_roles
    # matched_skills / missing_skills stored as JSON strings.
    # ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            analysis_id      INT AUTO_INCREMENT PRIMARY KEY,
            user_id          INT NOT NULL,
            role_id          INT NOT NULL,
            match_percentage DECIMAL(5,1) NOT NULL,
            matched_skills   TEXT,
            missing_skills   TEXT,
            analyzed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES job_roles(role_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("  ✓ analysis_history table created")


def seed_skills(cursor):
    """Insert all skills grouped by category."""
    print("\nSeeding skills...")

    skills = [
        # Programming Languages
        ('Python', 'Programming'), ('JavaScript', 'Programming'), ('Java', 'Programming'),
        ('C++', 'Programming'), ('TypeScript', 'Programming'), ('Go', 'Programming'),
        ('R', 'Programming'), ('PHP', 'Programming'),

        # Frontend
        ('HTML', 'Frontend'), ('CSS', 'Frontend'), ('React', 'Frontend'),
        ('Angular', 'Frontend'), ('Vue.js', 'Frontend'), ('Bootstrap', 'Frontend'),
        ('TailwindCSS', 'Frontend'),

        # Backend
        ('Node.js', 'Backend'), ('Django', 'Backend'), ('Flask', 'Backend'),
        ('Spring Boot', 'Backend'), ('Express.js', 'Backend'), ('FastAPI', 'Backend'),

        # Database
        ('SQL', 'Database'), ('MySQL', 'Database'), ('PostgreSQL', 'Database'),
        ('MongoDB', 'Database'), ('Redis', 'Database'), ('Firebase', 'Database'),
        ('Data Warehousing', 'Database'),

        # DevOps
        ('Docker', 'DevOps'), ('Kubernetes', 'DevOps'), ('Jenkins', 'DevOps'),
        ('Git', 'DevOps'), ('CI/CD', 'DevOps'), ('Terraform', 'DevOps'),
        ('Linux', 'DevOps'),

        # Cloud
        ('AWS', 'Cloud'), ('Azure', 'Cloud'), ('GCP', 'Cloud'),

        # Data Science
        ('Pandas', 'Data Science'), ('NumPy', 'Data Science'), ('Matplotlib', 'Data Science'),
        ('Scikit-learn', 'Data Science'), ('TensorFlow', 'Data Science'),
        ('PyTorch', 'Data Science'), ('Tableau', 'Data Science'), ('Power BI', 'Data Science'),
        ('Statistics', 'Data Science'), ('Machine Learning', 'Data Science'),
        ('Deep Learning', 'Data Science'), ('NLP', 'Data Science'),
        ('Computer Vision', 'Data Science'),

        # Mobile
        ('React Native', 'Mobile'), ('Flutter', 'Mobile'), ('Swift', 'Mobile'),
        ('Kotlin', 'Mobile'),

        # Architecture
        ('REST API', 'Architecture'), ('GraphQL', 'Architecture'),
        ('Microservices', 'Architecture'), ('System Design', 'Architecture'),

        # Methodology
        ('Agile/Scrum', 'Methodology'),

        # Computer Science
        ('Data Structures', 'Computer Science'), ('Algorithms', 'Computer Science'),

        # Security
        ('Network Security', 'Security'), ('Penetration Testing', 'Security'),
        ('Cryptography', 'Security'),
    ]

    for skill_name, category in skills:
        cursor.execute(
            "INSERT IGNORE INTO skills (skill_name, category) VALUES (%s, %s)",
            (skill_name, category)
        )

    print(f"  ✓ {len(skills)} skills seeded")


def seed_job_roles(cursor):
    """Insert job roles with descriptions."""
    print("\nSeeding job roles...")

    roles = [
        ('Frontend Developer',
         'Builds user interfaces and client-side experiences using HTML, CSS, JavaScript, and modern frameworks.',
         'Web Development'),
        ('Backend Developer',
         'Develops server-side logic, APIs, and database integrations for web applications.',
         'Web Development'),
        ('Full Stack Developer',
         'Works on both frontend and backend, handling the entire web application stack.',
         'Web Development'),
        ('Data Scientist',
         'Analyzes complex data sets, builds predictive models, and extracts business insights.',
         'Data & AI'),
        ('Data Analyst',
         'Collects, processes, and performs statistical analysis to help organizations make data-driven decisions.',
         'Data & AI'),
        ('DevOps Engineer',
         'Bridges development and operations with CI/CD pipelines, containerization, and infrastructure automation.',
         'Infrastructure'),
        ('Mobile App Developer',
         'Creates native and cross-platform mobile applications for iOS and Android.',
         'Mobile'),
        ('ML Engineer',
         'Designs, builds, and deploys machine learning models into production systems.',
         'Data & AI'),
        ('Cloud Architect',
         'Designs and manages cloud infrastructure, ensuring scalability, security, and cost efficiency.',
         'Infrastructure'),
        ('Cybersecurity Analyst',
         'Protects systems and networks from cyber threats through monitoring, testing, and implementing security measures.',
         'Security'),
        ('UI/UX Developer',
         'Combines design thinking with frontend development to create intuitive, user-centered digital experiences.',
         'Design'),
        ('Database Administrator',
         'Manages, optimizes, and secures database systems for performance and reliability.',
         'Infrastructure'),
    ]

    for role_name, description, category in roles:
        cursor.execute(
            "INSERT IGNORE INTO job_roles (role_name, description, category) VALUES (%s, %s, %s)",
            (role_name, description, category)
        )

    print(f"  ✓ {len(roles)} job roles seeded")


def seed_role_skills(cursor):
    """Map required skills to each job role with importance levels."""
    print("\nSeeding role-skill mappings...")

    # Helper: look up skill_id by name
    cursor.execute("SELECT skill_id, skill_name FROM skills")
    skill_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Helper: look up role_id by name
    cursor.execute("SELECT role_id, role_name FROM job_roles")
    role_map = {row[1]: row[0] for row in cursor.fetchall()}

    # (role_name, skill_name, importance)
    mappings = [
        # ── Frontend Developer ──
        ('Frontend Developer', 'HTML', 'Critical'),
        ('Frontend Developer', 'CSS', 'Critical'),
        ('Frontend Developer', 'JavaScript', 'Critical'),
        ('Frontend Developer', 'React', 'Critical'),
        ('Frontend Developer', 'TypeScript', 'Important'),
        ('Frontend Developer', 'Bootstrap', 'Important'),
        ('Frontend Developer', 'TailwindCSS', 'Nice to Have'),
        ('Frontend Developer', 'Git', 'Important'),
        ('Frontend Developer', 'REST API', 'Important'),
        ('Frontend Developer', 'Agile/Scrum', 'Nice to Have'),

        # ── Backend Developer ──
        ('Backend Developer', 'Python', 'Critical'),
        ('Backend Developer', 'Java', 'Important'),
        ('Backend Developer', 'SQL', 'Critical'),
        ('Backend Developer', 'MySQL', 'Critical'),
        ('Backend Developer', 'PostgreSQL', 'Important'),
        ('Backend Developer', 'Node.js', 'Important'),
        ('Backend Developer', 'REST API', 'Critical'),
        ('Backend Developer', 'Git', 'Important'),
        ('Backend Developer', 'Docker', 'Nice to Have'),
        ('Backend Developer', 'Microservices', 'Nice to Have'),

        # ── Full Stack Developer ──
        ('Full Stack Developer', 'HTML', 'Critical'),
        ('Full Stack Developer', 'CSS', 'Critical'),
        ('Full Stack Developer', 'JavaScript', 'Critical'),
        ('Full Stack Developer', 'Python', 'Important'),
        ('Full Stack Developer', 'React', 'Critical'),
        ('Full Stack Developer', 'Node.js', 'Important'),
        ('Full Stack Developer', 'SQL', 'Important'),
        ('Full Stack Developer', 'MySQL', 'Important'),
        ('Full Stack Developer', 'MongoDB', 'Nice to Have'),
        ('Full Stack Developer', 'Git', 'Important'),
        ('Full Stack Developer', 'Docker', 'Nice to Have'),
        ('Full Stack Developer', 'REST API', 'Critical'),

        # ── Data Scientist ──
        ('Data Scientist', 'Python', 'Critical'),
        ('Data Scientist', 'R', 'Important'),
        ('Data Scientist', 'SQL', 'Important'),
        ('Data Scientist', 'Pandas', 'Critical'),
        ('Data Scientist', 'NumPy', 'Critical'),
        ('Data Scientist', 'Matplotlib', 'Important'),
        ('Data Scientist', 'Scikit-learn', 'Critical'),
        ('Data Scientist', 'Statistics', 'Critical'),
        ('Data Scientist', 'Machine Learning', 'Critical'),
        ('Data Scientist', 'TensorFlow', 'Important'),

        # ── Data Analyst ──
        ('Data Analyst', 'Python', 'Critical'),
        ('Data Analyst', 'SQL', 'Critical'),
        ('Data Analyst', 'MySQL', 'Important'),
        ('Data Analyst', 'Pandas', 'Critical'),
        ('Data Analyst', 'NumPy', 'Important'),
        ('Data Analyst', 'Matplotlib', 'Important'),
        ('Data Analyst', 'Tableau', 'Important'),
        ('Data Analyst', 'Power BI', 'Nice to Have'),
        ('Data Analyst', 'Statistics', 'Critical'),
        ('Data Analyst', 'Data Warehousing', 'Nice to Have'),

        # ── DevOps Engineer ──
        ('DevOps Engineer', 'Python', 'Important'),
        ('DevOps Engineer', 'Linux', 'Critical'),
        ('DevOps Engineer', 'Docker', 'Critical'),
        ('DevOps Engineer', 'Kubernetes', 'Critical'),
        ('DevOps Engineer', 'Jenkins', 'Important'),
        ('DevOps Engineer', 'Git', 'Critical'),
        ('DevOps Engineer', 'CI/CD', 'Critical'),
        ('DevOps Engineer', 'AWS', 'Important'),
        ('DevOps Engineer', 'Terraform', 'Important'),
        ('DevOps Engineer', 'Microservices', 'Nice to Have'),

        # ── Mobile App Developer ──
        ('Mobile App Developer', 'JavaScript', 'Critical'),
        ('Mobile App Developer', 'React Native', 'Critical'),
        ('Mobile App Developer', 'Flutter', 'Important'),
        ('Mobile App Developer', 'Swift', 'Important'),
        ('Mobile App Developer', 'Kotlin', 'Important'),
        ('Mobile App Developer', 'Git', 'Important'),
        ('Mobile App Developer', 'REST API', 'Critical'),
        ('Mobile App Developer', 'Firebase', 'Important'),
        ('Mobile App Developer', 'CSS', 'Nice to Have'),
        ('Mobile App Developer', 'Agile/Scrum', 'Nice to Have'),

        # ── ML Engineer ──
        ('ML Engineer', 'Python', 'Critical'),
        ('ML Engineer', 'TensorFlow', 'Critical'),
        ('ML Engineer', 'PyTorch', 'Critical'),
        ('ML Engineer', 'Scikit-learn', 'Important'),
        ('ML Engineer', 'Machine Learning', 'Critical'),
        ('ML Engineer', 'Deep Learning', 'Critical'),
        ('ML Engineer', 'NumPy', 'Important'),
        ('ML Engineer', 'Pandas', 'Important'),
        ('ML Engineer', 'Docker', 'Nice to Have'),
        ('ML Engineer', 'AWS', 'Nice to Have'),

        # ── Cloud Architect ──
        ('Cloud Architect', 'AWS', 'Critical'),
        ('Cloud Architect', 'Azure', 'Critical'),
        ('Cloud Architect', 'GCP', 'Important'),
        ('Cloud Architect', 'Docker', 'Critical'),
        ('Cloud Architect', 'Kubernetes', 'Critical'),
        ('Cloud Architect', 'Terraform', 'Important'),
        ('Cloud Architect', 'Linux', 'Important'),
        ('Cloud Architect', 'Microservices', 'Important'),
        ('Cloud Architect', 'System Design', 'Critical'),
        ('Cloud Architect', 'CI/CD', 'Important'),

        # ── Cybersecurity Analyst ──
        ('Cybersecurity Analyst', 'Python', 'Important'),
        ('Cybersecurity Analyst', 'Linux', 'Critical'),
        ('Cybersecurity Analyst', 'SQL', 'Important'),
        ('Cybersecurity Analyst', 'Network Security', 'Critical'),
        ('Cybersecurity Analyst', 'Penetration Testing', 'Critical'),
        ('Cybersecurity Analyst', 'Cryptography', 'Critical'),
        ('Cybersecurity Analyst', 'Docker', 'Nice to Have'),
        ('Cybersecurity Analyst', 'AWS', 'Nice to Have'),
        ('Cybersecurity Analyst', 'Git', 'Important'),
        ('Cybersecurity Analyst', 'CI/CD', 'Nice to Have'),

        # ── UI/UX Developer ──
        ('UI/UX Developer', 'HTML', 'Critical'),
        ('UI/UX Developer', 'CSS', 'Critical'),
        ('UI/UX Developer', 'JavaScript', 'Critical'),
        ('UI/UX Developer', 'TypeScript', 'Important'),
        ('UI/UX Developer', 'React', 'Important'),
        ('UI/UX Developer', 'Bootstrap', 'Important'),
        ('UI/UX Developer', 'TailwindCSS', 'Important'),
        ('UI/UX Developer', 'Git', 'Important'),
        ('UI/UX Developer', 'Agile/Scrum', 'Nice to Have'),
        ('UI/UX Developer', 'Vue.js', 'Nice to Have'),

        # ── Database Administrator ──
        ('Database Administrator', 'SQL', 'Critical'),
        ('Database Administrator', 'MySQL', 'Critical'),
        ('Database Administrator', 'PostgreSQL', 'Critical'),
        ('Database Administrator', 'MongoDB', 'Important'),
        ('Database Administrator', 'Redis', 'Important'),
        ('Database Administrator', 'Python', 'Important'),
        ('Database Administrator', 'Linux', 'Important'),
        ('Database Administrator', 'Docker', 'Nice to Have'),
        ('Database Administrator', 'Data Warehousing', 'Important'),
        ('Database Administrator', 'AWS', 'Nice to Have'),
    ]

    count = 0
    for role_name, skill_name, importance in mappings:
        role_id = role_map.get(role_name)
        skill_id = skill_map.get(skill_name)
        if role_id and skill_id:
            cursor.execute(
                "INSERT IGNORE INTO role_skills (role_id, skill_id, importance_level) VALUES (%s, %s, %s)",
                (role_id, skill_id, importance)
            )
            count += 1

    print(f"  ✓ {count} role-skill mappings seeded")


def seed_learning_resources(cursor):
    """Insert curated learning resources for skills."""
    print("\nSeeding learning resources...")

    cursor.execute("SELECT skill_id, skill_name FROM skills")
    skill_map = {row[1]: row[0] for row in cursor.fetchall()}

    # (skill_name, title, url, platform, resource_type)
    resources = [
        # Python
        ('Python', 'Python Official Tutorial',
         'https://docs.python.org/3/tutorial/', 'Python.org', 'Documentation'),
        ('Python', 'Complete Python Bootcamp (Udemy)',
         'https://www.udemy.com/course/complete-python-bootcamp/', 'Udemy', 'Course'),

        # JavaScript
        ('JavaScript', 'MDN JavaScript Guide',
         'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', 'MDN', 'Documentation'),
        ('JavaScript', 'JavaScript.info – Modern Tutorial',
         'https://javascript.info/', 'JavaScript.info', 'Tutorial'),

        # Java
        ('Java', 'Java Programming MOOC',
         'https://java-programming.mooc.fi/', 'University of Helsinki', 'Course'),
        ('Java', 'Oracle Java Tutorials',
         'https://docs.oracle.com/javase/tutorial/', 'Oracle', 'Documentation'),

        # TypeScript
        ('TypeScript', 'TypeScript Handbook',
         'https://www.typescriptlang.org/docs/handbook/', 'TypeScript', 'Documentation'),

        # HTML
        ('HTML', 'Responsive Web Design (freeCodeCamp)',
         'https://www.freecodecamp.org/learn/2022/responsive-web-design/', 'freeCodeCamp', 'Course'),
        ('HTML', 'MDN HTML Basics',
         'https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics', 'MDN', 'Documentation'),

        # CSS
        ('CSS', 'CSS Complete Guide (MDN)',
         'https://developer.mozilla.org/en-US/docs/Web/CSS', 'MDN', 'Documentation'),
        ('CSS', 'CSS for JavaScript Developers',
         'https://css-for-js.dev/', 'Josh Comeau', 'Course'),

        # React
        ('React', 'React Official Tutorial',
         'https://react.dev/learn', 'React.dev', 'Documentation'),
        ('React', 'React – The Complete Guide (Udemy)',
         'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', 'Udemy', 'Course'),

        # Angular
        ('Angular', 'Angular Official Tutorial',
         'https://angular.dev/tutorials', 'Angular', 'Documentation'),

        # Vue.js
        ('Vue.js', 'Vue.js Official Guide',
         'https://vuejs.org/guide/introduction.html', 'Vue.js', 'Documentation'),

        # Node.js
        ('Node.js', 'Node.js Official Guides',
         'https://nodejs.org/en/learn', 'Node.js', 'Documentation'),
        ('Node.js', 'The Complete Node.js Developer Course',
         'https://www.udemy.com/course/the-complete-nodejs-developer-course-2/', 'Udemy', 'Course'),

        # Django
        ('Django', 'Django Official Tutorial',
         'https://docs.djangoproject.com/en/stable/intro/tutorial01/', 'Django', 'Documentation'),

        # Flask
        ('Flask', 'Flask Official Tutorial',
         'https://flask.palletsprojects.com/en/latest/tutorial/', 'Flask', 'Documentation'),

        # SQL
        ('SQL', 'SQL Tutorial (W3Schools)',
         'https://www.w3schools.com/sql/', 'W3Schools', 'Tutorial'),
        ('SQL', 'SQL for Data Science (Coursera)',
         'https://www.coursera.org/learn/sql-for-data-science', 'Coursera', 'Course'),

        # MySQL
        ('MySQL', 'MySQL Official Documentation',
         'https://dev.mysql.com/doc/', 'MySQL', 'Documentation'),

        # PostgreSQL
        ('PostgreSQL', 'PostgreSQL Official Tutorial',
         'https://www.postgresql.org/docs/current/tutorial.html', 'PostgreSQL', 'Documentation'),

        # MongoDB
        ('MongoDB', 'MongoDB University – Free Courses',
         'https://university.mongodb.com/', 'MongoDB', 'Course'),

        # Docker
        ('Docker', 'Docker Getting Started Guide',
         'https://docs.docker.com/get-started/', 'Docker', 'Documentation'),
        ('Docker', 'Docker Mastery (Udemy)',
         'https://www.udemy.com/course/docker-mastery/', 'Udemy', 'Course'),

        # Kubernetes
        ('Kubernetes', 'Kubernetes Official Tutorials',
         'https://kubernetes.io/docs/tutorials/', 'Kubernetes', 'Documentation'),

        # Git
        ('Git', 'Pro Git Book (free)',
         'https://git-scm.com/book/en/v2', 'Git SCM', 'Book'),
        ('Git', 'Git & GitHub Crash Course',
         'https://www.youtube.com/watch?v=RGOj5yH7evk', 'YouTube', 'Video'),

        # AWS
        ('AWS', 'AWS Cloud Practitioner Essentials',
         'https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/', 'AWS', 'Course'),
        ('AWS', 'AWS Documentation',
         'https://docs.aws.amazon.com/', 'AWS', 'Documentation'),

        # Azure
        ('Azure', 'Microsoft Azure Fundamentals',
         'https://learn.microsoft.com/en-us/training/paths/az-900-describe-cloud-concepts/', 'Microsoft Learn', 'Course'),

        # GCP
        ('GCP', 'Google Cloud Skills Boost',
         'https://www.cloudskillsboost.google/', 'Google Cloud', 'Course'),

        # Pandas
        ('Pandas', 'Pandas Getting Started',
         'https://pandas.pydata.org/docs/getting_started/', 'Pandas', 'Documentation'),
        ('Pandas', 'Learn Pandas (Kaggle)',
         'https://www.kaggle.com/learn/pandas', 'Kaggle', 'Course'),

        # NumPy
        ('NumPy', 'NumPy Quickstart Tutorial',
         'https://numpy.org/doc/stable/user/quickstart.html', 'NumPy', 'Documentation'),

        # Matplotlib
        ('Matplotlib', 'Matplotlib Official Tutorials',
         'https://matplotlib.org/stable/tutorials/', 'Matplotlib', 'Documentation'),

        # Scikit-learn
        ('Scikit-learn', 'Scikit-learn Tutorials',
         'https://scikit-learn.org/stable/tutorial/', 'Scikit-learn', 'Documentation'),

        # TensorFlow
        ('TensorFlow', 'TensorFlow Official Tutorials',
         'https://www.tensorflow.org/tutorials', 'TensorFlow', 'Documentation'),

        # PyTorch
        ('PyTorch', 'PyTorch Official Tutorials',
         'https://pytorch.org/tutorials/', 'PyTorch', 'Documentation'),

        # Machine Learning
        ('Machine Learning', 'Machine Learning by Andrew Ng',
         'https://www.coursera.org/learn/machine-learning', 'Coursera', 'Course'),
        ('Machine Learning', 'Google ML Crash Course',
         'https://developers.google.com/machine-learning/crash-course', 'Google', 'Course'),

        # Deep Learning
        ('Deep Learning', 'Deep Learning Specialization',
         'https://www.coursera.org/specializations/deep-learning', 'Coursera', 'Course'),

        # Statistics
        ('Statistics', 'Statistics & Probability (Khan Academy)',
         'https://www.khanacademy.org/math/statistics-probability', 'Khan Academy', 'Course'),

        # Linux
        ('Linux', 'Linux Journey – Free Tutorials',
         'https://linuxjourney.com/', 'Linux Journey', 'Tutorial'),

        # REST API
        ('REST API', 'RESTful API Design Guide',
         'https://restfulapi.net/', 'RESTful API', 'Tutorial'),

        # Data Structures
        ('Data Structures', 'Data Structures (GeeksforGeeks)',
         'https://www.geeksforgeeks.org/data-structures/', 'GeeksforGeeks', 'Tutorial'),

        # Algorithms
        ('Algorithms', 'Introduction to Algorithms (MIT OCW)',
         'https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/', 'MIT OCW', 'Course'),

        # Network Security
        ('Network Security', 'Cybersecurity Fundamentals',
         'https://www.coursera.org/learn/cyber-security-domain', 'Coursera', 'Course'),

        # Penetration Testing
        ('Penetration Testing', 'TryHackMe – Learn Pentesting',
         'https://tryhackme.com/', 'TryHackMe', 'Tutorial'),

        # Cryptography
        ('Cryptography', 'Cryptography I (Stanford/Coursera)',
         'https://www.coursera.org/learn/crypto', 'Coursera', 'Course'),

        # Tableau
        ('Tableau', 'Tableau Public – Free Learning',
         'https://public.tableau.com/app/resources/learn', 'Tableau', 'Tutorial'),

        # Power BI
        ('Power BI', 'Power BI Guided Learning',
         'https://learn.microsoft.com/en-us/power-bi/guided-learning/', 'Microsoft Learn', 'Course'),

        # React Native
        ('React Native', 'React Native Official Docs',
         'https://reactnative.dev/docs/getting-started', 'React Native', 'Documentation'),

        # Flutter
        ('Flutter', 'Flutter Official Codelabs',
         'https://docs.flutter.dev/get-started/codelab', 'Flutter', 'Documentation'),

        # Swift
        ('Swift', 'Swift Programming Language Guide',
         'https://docs.swift.org/swift-book/', 'Apple', 'Documentation'),

        # Kotlin
        ('Kotlin', 'Kotlin Official Docs',
         'https://kotlinlang.org/docs/getting-started.html', 'Kotlin', 'Documentation'),

        # CI/CD
        ('CI/CD', 'GitHub Actions Documentation',
         'https://docs.github.com/en/actions', 'GitHub', 'Documentation'),

        # Microservices
        ('Microservices', 'Microservices Guide (Martin Fowler)',
         'https://martinfowler.com/microservices/', 'Martin Fowler', 'Tutorial'),

        # System Design
        ('System Design', 'System Design Primer (GitHub)',
         'https://github.com/donnemartin/system-design-primer', 'GitHub', 'Tutorial'),

        # Firebase
        ('Firebase', 'Firebase Documentation',
         'https://firebase.google.com/docs', 'Google', 'Documentation'),

        # Bootstrap
        ('Bootstrap', 'Bootstrap Official Docs',
         'https://getbootstrap.com/docs/', 'Bootstrap', 'Documentation'),

        # TailwindCSS
        ('TailwindCSS', 'Tailwind CSS Documentation',
         'https://tailwindcss.com/docs', 'Tailwind CSS', 'Documentation'),

        # Terraform
        ('Terraform', 'Terraform Getting Started',
         'https://developer.hashicorp.com/terraform/tutorials', 'HashiCorp', 'Tutorial'),

        # Redis
        ('Redis', 'Redis University',
         'https://university.redis.com/', 'Redis', 'Course'),

        # GraphQL
        ('GraphQL', 'How to GraphQL',
         'https://www.howtographql.com/', 'How to GraphQL', 'Tutorial'),

        # Agile/Scrum
        ('Agile/Scrum', 'Agile with Atlassian Jira',
         'https://www.coursera.org/learn/agile-atlassian-jira', 'Coursera', 'Course'),

        # NLP
        ('NLP', 'NLP with Python (spaCy)',
         'https://course.spacy.io/', 'spaCy', 'Course'),

        # Computer Vision
        ('Computer Vision', 'OpenCV Tutorials',
         'https://docs.opencv.org/4.x/d9/df8/tutorial_root.html', 'OpenCV', 'Documentation'),
    ]

    count = 0
    for skill_name, title, url, platform, res_type in resources:
        skill_id = skill_map.get(skill_name)
        if skill_id:
            cursor.execute(
                "INSERT IGNORE INTO learning_resources (skill_id, title, url, platform, resource_type) "
                "VALUES (%s, %s, %s, %s, %s)",
                (skill_id, title, url, platform, res_type)
            )
            count += 1

    print(f"  ✓ {count} learning resources seeded")


def verify_setup(cursor):
    """Run verification queries to confirm data integrity."""
    print("\n" + "=" * 50)
    print("VERIFICATION")
    print("=" * 50)

    cursor.execute("SELECT COUNT(*) FROM skills")
    print(f"  Skills:             {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM job_roles")
    print(f"  Job Roles:          {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM role_skills")
    print(f"  Role-Skill Maps:    {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM learning_resources")
    print(f"  Learning Resources: {cursor.fetchone()[0]}")

    print("\n  Sample — Skills per Role:")
    cursor.execute("""
        SELECT jr.role_name, COUNT(rs.skill_id) AS skill_count
        FROM job_roles jr
        LEFT JOIN role_skills rs ON jr.role_id = rs.role_id
        GROUP BY jr.role_name
        ORDER BY jr.role_name
    """)
    for row in cursor.fetchall():
        print(f"    {row[0]:30s} → {row[1]} skills")


def main():
    """Run the full database setup."""
    print("=" * 50)
    print("  SKILL GAP ANALYZER — DATABASE SETUP")
    print("=" * 50)

    # Step 1: Connect without database to create it
    conn = get_connection(use_database=False)
    cursor = conn.cursor()

    create_database(cursor)
    create_tables(cursor)
    seed_skills(cursor)
    seed_job_roles(cursor)
    seed_role_skills(cursor)
    seed_learning_resources(cursor)

    conn.commit()
    verify_setup(cursor)

    cursor.close()
    conn.close()

    print("\n" + "=" * 50)
    print("  ✅ DATABASE SETUP COMPLETE!")
    print("  You can now run: python app.py")
    print("=" * 50)


if __name__ == '__main__':
    main()
