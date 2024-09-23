import psycopg2
from datetime import datetime
import click

# Database connection setup
def create_connection():
    return psycopg2.connect(
        dbname='tracker',
        user='postgres',
        password='12345',
        host='localhost'
    )

# Create tables
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            activity_id INTEGER REFERENCES activities(id),
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP
        );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    click.echo("Tables created successfully.")

# Model functions
def add_activity(name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activities (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (name,))
    conn.commit()
    cursor.close()
    conn.close()

def start_session(activity_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM activities WHERE name = %s;", (activity_name,))
    activity = cursor.fetchone()

    if activity:
        start_time = datetime.now()
        cursor.execute("INSERT INTO sessions (activity_id, start_time) VALUES (%s, %s);",
                       (activity[0], start_time))
        conn.commit()
        cursor.close()
        conn.close()
        return start_time
    else:
        print("Activity not found.")
        cursor.close()
        conn.close()
        return None

def stop_session(activity_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM activities WHERE name = %s;", (activity_name,))
    activity = cursor.fetchone()

    if activity:
        end_time = datetime.now()
        cursor.execute("UPDATE sessions SET end_time = %s WHERE activity_id = %s AND end_time IS NULL;",
                       (end_time, activity[0]))
        conn.commit()
        cursor.close()
        conn.close()
        return end_time
    else:
        print("Activity not found.")
        cursor.close()
        conn.close()
        return None

def view_history():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.name, s.start_time, s.end_time 
        FROM sessions s 
        JOIN activities a ON s.activity_id = a.id;
    """)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

def generate_report():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.name, SUM(EXTRACT(EPOCH FROM (s.end_time - s.start_time))) AS total_seconds
        FROM sessions s 
        JOIN activities a ON s.activity_id = a.id 
        WHERE s.end_time IS NOT NULL
        GROUP BY a.name;
    """)
    report = cursor.fetchall()
    cursor.close()
    conn.close()
    return report

# New function to delete an activity
def delete_activity(name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activities WHERE name = %s;", (name,))
    conn.commit()
    cursor.close()
    conn.close()

# New function to update an activity's name
def update_activity(old_name, new_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE activities SET name = %s WHERE name = %s;", (new_name, old_name))
    conn.commit()
    cursor.close()
    conn.close()

# CLI setup
@click.group()
def cli():
    """Time-Tracking CLI Application"""
    pass

@cli.command()
@click.argument('name')
def add(name):
    """Add a new activity."""
    add_activity(name)
    click.echo(f"Activity '{name}' added.")

@cli.command()
@click.argument('activity_name')
def start(activity_name):
    """Start tracking an activity."""
    start_time = start_session(activity_name)
    if start_time:
        click.echo(f"Started tracking '{activity_name}' at {start_time}.")

@cli.command()
@click.argument('activity_name')
def stop(activity_name):
    """Stop tracking an activity."""
    end_time = stop_session(activity_name)
    if end_time:
        click.echo(f"Stopped tracking '{activity_name}' at {end_time}.")

@cli.command()
def history():
    """View session history."""
    records = view_history()
    for record in records:
        click.echo(f"Activity: {record[0]}, Start: {record[1]}, End: {record[2]}")

@cli.command()
def report():
    """Generate a productivity report."""
    report_data = generate_report()
    for item in report_data:
        click.echo(f"Activity: {item[0]}, Total Time: {item[1] // 3600}h {item[1] % 3600 // 60}m")

# New CLI command for deleting an activity
@cli.command()
@click.argument('name')
def delete(name):
    """Delete an activity."""
    delete_activity(name)
    click.echo(f"Activity '{name}' deleted.")

# New CLI command for updating an activity's name
@cli.command()
@click.argument('old_name')
@click.argument('new_name')
def update(old_name, new_name):
    """Update the name of an activity."""
    update_activity(old_name, new_name)
    click.echo(f"Activity '{old_name}' updated to '{new_name}'.")

if __name__ == '__main__':
    create_tables()  # Create tables when running the script
    cli()
