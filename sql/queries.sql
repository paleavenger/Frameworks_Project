-- 1. Список студентов
SELECT
    id,
    name,
    specialty
FROM students
ORDER BY name;

-- 2. Список проектов
SELECT
    id,
    title
FROM projects
ORDER BY title;

-- 3. Список ролей
SELECT
    id,
    name
FROM roles
ORDER BY id;

-- 4. Сводка по командам
SELECT
    id,
    name,
    project_title,
    members_count,
    readiness_percent,
    readiness_message
FROM team_overview
ORDER BY name;

-- 5. Лидеры по готовности
SELECT
    name,
    readiness_percent
FROM team_overview
ORDER BY readiness_percent DESC, name
LIMIT 3 OFFSET 0;

-- 6. Студенты заданной специальности
SELECT
    id,
    name,
    specialty
FROM students
WHERE specialty = 'разработка'
ORDER BY name;

-- 7. Студенты по первой букве имени
SELECT
    id,
    name
FROM students
WHERE name LIKE 'Бр%'
ORDER BY name;

-- 8. Студенты без команды
SELECT
    id,
    name,
    specialty
FROM students
WHERE id NOT IN (
    SELECT student_id
    FROM team_members
)
ORDER BY name;

-- 9. Участники без роли
SELECT
    students.name AS student_name,
    teams.name AS team_name
FROM team_members
JOIN students ON students.id = team_members.student_id
JOIN teams ON teams.id = team_members.team_id
WHERE team_members.role_id IS NULL
ORDER BY teams.name, students.name;

-- 10. Команды с двумя и более свободными местами
SELECT
    id,
    name,
    members_count,
    5 - members_count AS free_places
FROM team_overview
WHERE 5 - members_count >= 2
ORDER BY free_places DESC, name;

-- 11. Неготовые команды
SELECT
    name,
    readiness_percent,
    readiness_message
FROM team_overview
WHERE readiness_percent < 100
ORDER BY readiness_percent, name;

-- 12. Уникальные специальности
SELECT DISTINCT specialty
FROM students
WHERE specialty <> ''
ORDER BY specialty;

-- 13. Студенты и их команды
SELECT
    students.id,
    students.name,
    students.specialty,
    teams.name AS team_name
FROM students
LEFT JOIN team_members ON team_members.student_id = students.id
LEFT JOIN teams ON teams.id = team_members.team_id
ORDER BY students.name;

-- 14. Карточка студента
SELECT
    students.id,
    students.name,
    students.specialty,
    teams.id AS team_id,
    teams.name AS team_name,
    roles.name AS role_name
FROM students
LEFT JOIN team_members ON team_members.student_id = students.id
LEFT JOIN teams ON teams.id = team_members.team_id
LEFT JOIN roles ON roles.id = team_members.role_id
WHERE students.id = 1;

-- 15. Состав команды
SELECT
    students.id AS student_id,
    students.name AS student_name,
    students.specialty,
    roles.name AS role_name
FROM team_members
JOIN students ON students.id = team_members.student_id
LEFT JOIN roles ON roles.id = team_members.role_id
WHERE team_members.team_id = 1
ORDER BY students.name;

-- 16. Участники с командами, проектами и ролями
SELECT
    teams.name AS team_name,
    projects.title AS project_title,
    students.name AS student_name,
    roles.name AS role_name
FROM team_members
JOIN teams ON teams.id = team_members.team_id
JOIN projects ON projects.id = teams.project_id
JOIN students ON students.id = team_members.student_id
LEFT JOIN roles ON roles.id = team_members.role_id
ORDER BY teams.name, students.name;

-- 17. Команды выбранного проекта
SELECT
    teams.id,
    teams.name
FROM teams
JOIN projects ON projects.id = teams.project_id
WHERE projects.id = 1
ORDER BY teams.name;

-- 18. Число студентов, команд и проектов
SELECT
    (SELECT COUNT(*) FROM students) AS students_count,
    (SELECT COUNT(*) FROM teams) AS teams_count,
    (SELECT COUNT(*) FROM projects) AS projects_count;

-- 19. Число студентов без команды
SELECT COUNT(*) AS free_students_count
FROM students
WHERE id NOT IN (
    SELECT student_id
    FROM team_members
);

-- 20. Число участников без роли
SELECT
    COUNT(*) AS members_count,
    COUNT(role_id) AS roles_assigned,
    COUNT(*) - COUNT(role_id) AS without_role_count
FROM team_members;

-- 21. Размеры команд
SELECT
    CAST(ROUND(AVG(members_count)) AS INTEGER) AS avg_size,
    MIN(members_count) AS min_size,
    MAX(members_count) AS max_size
FROM team_overview;

-- 22. Число студентов по специальностям
SELECT
    specialty,
    COUNT(*) AS students_count
FROM students
GROUP BY specialty
ORDER BY students_count DESC, specialty;

-- 23. Число участников по ролям
SELECT
    roles.name AS role_name,
    COUNT(team_members.id) AS members_count
FROM roles
LEFT JOIN team_members ON team_members.role_id = roles.id
GROUP BY roles.id, roles.name
ORDER BY members_count DESC, roles.name;

-- 24. Число команд по проектам
SELECT
    projects.id,
    projects.title,
    COUNT(teams.id) AS teams_count
FROM projects
LEFT JOIN teams ON teams.project_id = projects.id
GROUP BY projects.id, projects.title
ORDER BY projects.title;

-- 25. Проекты с несколькими командами
SELECT
    projects.title,
    COUNT(teams.id) AS teams_count
FROM projects
JOIN teams ON teams.project_id = projects.id
GROUP BY projects.id, projects.title
HAVING COUNT(teams.id) > 1
ORDER BY teams_count DESC, projects.title;

-- 26. Неготовые команды по составу и ролям
SELECT
    teams.name,
    COUNT(team_members.id) AS members_count,
    COUNT(team_members.role_id) AS roles_assigned
FROM teams
LEFT JOIN team_members ON team_members.team_id = teams.id
GROUP BY teams.id, teams.name
HAVING COUNT(team_members.id) < 3
    OR COUNT(team_members.role_id) < COUNT(team_members.id)
ORDER BY teams.name;
