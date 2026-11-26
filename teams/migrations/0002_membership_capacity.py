from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("teams", "0001_initial")]

    operations = [
        migrations.RunSQL(
            sql=[
                """
                CREATE TRIGGER teams_membership_capacity_insert
                BEFORE INSERT ON teams_membership
                WHEN (
                    SELECT COUNT(*) FROM teams_membership
                    WHERE team_id = NEW.team_id
                ) >= 5
                BEGIN
                    SELECT RAISE(ABORT, 'В команде не более 5 участников');
                END;
                """,
                """
                CREATE TRIGGER teams_membership_capacity_update
                BEFORE UPDATE OF team_id ON teams_membership
                WHEN NEW.team_id <> OLD.team_id AND (
                    SELECT COUNT(*) FROM teams_membership
                    WHERE team_id = NEW.team_id
                ) >= 5
                BEGIN
                    SELECT RAISE(ABORT, 'В команде не более 5 участников');
                END;
                """,
            ],
            reverse_sql=[
                "DROP TRIGGER teams_membership_capacity_insert;",
                "DROP TRIGGER teams_membership_capacity_update;",
            ],
        ),
    ]
