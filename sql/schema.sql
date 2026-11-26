-- Лимиты совпадают с MIN_SIZE и MAX_SIZE класса Team

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL UNIQUE,
    role_id INTEGER,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE INDEX IF NOT EXISTS idx_team_members_team_id
    ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_teams_project_id
    ON teams(project_id);

CREATE TRIGGER IF NOT EXISTS team_members_max_size_insert
BEFORE INSERT ON team_members
WHEN (SELECT COUNT(*) FROM team_members WHERE team_id = NEW.team_id) >= 5
BEGIN
    SELECT RAISE(ABORT, 'В команде не более 5 участников');
END;

CREATE TRIGGER IF NOT EXISTS team_members_max_size_update
BEFORE UPDATE OF team_id ON team_members
WHEN NEW.team_id <> OLD.team_id
 AND (SELECT COUNT(*) FROM team_members WHERE team_id = NEW.team_id) >= 5
BEGIN
    SELECT RAISE(ABORT, 'В команде не более 5 участников');
END;

DROP VIEW IF EXISTS team_overview;
CREATE VIEW team_overview AS
SELECT
    teams.id,
    teams.name,
    teams.project_id,
    projects.title AS project_title,
    COUNT(team_members.id) AS members_count,
    COUNT(team_members.role_id) AS roles_count,
    COUNT(team_members.role_id) * 100
        / MAX(COUNT(team_members.id), 3) AS readiness_percent,
    CASE
        WHEN COUNT(team_members.id) = 0
            THEN 'Команда пока пуста'
        WHEN COUNT(team_members.id) < 3
            THEN 'Нужно не менее 3 участников'
        WHEN COUNT(team_members.role_id) < COUNT(team_members.id)
            THEN 'Нужно назначить роли'
        ELSE 'Команда готова к работе'
    END AS readiness_message
FROM teams
JOIN projects ON projects.id = teams.project_id
LEFT JOIN team_members ON team_members.team_id = teams.id
GROUP BY teams.id, teams.name, teams.project_id, projects.title;
