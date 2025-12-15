# attendance_db.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date, time as dtime, timedelta

DB_CONFIG = {
    "host": "kennardb-mysql-moonlitguardian23-9f54.e.aivencloud.com",
    "port": 12769,
    "user": "avnadmin",
    "password": "AVNS_Qyja81mEQ4otUCCMC1S",
    "database": "defaultdb",
    "ssl_ca": "ca.pem"
}


def log_attendance(employee_id, fullname, temperature, mode):
    """
    Logs employee attendance in the database.
    mode = "Time-In" → insert if not already today
    mode = "Time-Out" → update today's record
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        today = datetime.now().date()
        now = datetime.now()
        now_time = now.strftime("%H:%M:%S")

        # 1️⃣ Check if record exists today
        cursor.execute("""
            SELECT id, employee_id, time_in, time_out, status 
            FROM attendance 
            WHERE employee_id = %s AND date = %s
        """, (employee_id, today))
        record = cursor.fetchone()

        # 2️⃣ Handle Time-In
        if mode == "Time-In":
            if record:
                print("✅ Already Time-In today, skipping insert.")
            else:
                late_threshold = datetime.combine(today, dtime(8, 15))
                status = "Present" if now <= late_threshold else "Late"

                cursor.execute("""
                    INSERT INTO attendance (date, employee_id, fullname, temperature, status, time_in)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (today, employee_id, fullname, temperature, status, now_time))
                print(f"✅ Time-In logged successfully ({status}).")

        # 3️⃣ Handle Time-Out
        elif mode == "Time-Out":
            if record:
                record_id, emp_id, time_in_val, _, status_val = record
                working_hours = None
                if time_in_val:
                    t_in = datetime.strptime(str(time_in_val), "%H:%M:%S")
                    t_out = datetime.strptime(now_time, "%H:%M:%S")
                    diff = (t_out - t_in).seconds / 3600.0
                    working_hours = round(diff, 2)

                cursor.execute("""
                    UPDATE attendance 
                    SET time_out = %s, working_hours = %s 
                    WHERE id = %s
                """, (now_time, working_hours, record_id))
                print(f"✅ Time-Out logged successfully ({status_val}).")
            else:
                cursor.execute("""
                    INSERT INTO attendance (date, employee_id, fullname, temperature, status, time_out)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (today, employee_id, fullname, temperature, "Present", now_time))
                print("⚠️ No Time-In found, created record with Time-Out.")

        conn.commit()
        cursor.close()
        conn.close()

    except Error as e:
        print("❌ Database error while logging attendance:", e)



# --- ✅ Check if employee already has Time-In today ---
def has_time_in_today(employee_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        today = datetime.now().date()
        cursor.execute("""
            SELECT time_in FROM attendance 
            WHERE employee_id = %s AND date = %s AND time_in IS NOT NULL
        """, (employee_id, today))
        record = cursor.fetchone()
        cursor.close()
        conn.close()
        return record is not None
    except Error as e:
        print("❌ Database error in has_time_in_today:", e)
        return False


# --- ✅ Check if employee already has Time-Out today ---
def has_time_out_today(employee_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        today = datetime.now().date()
        cursor.execute("""
            SELECT time_out FROM attendance 
            WHERE employee_id = %s AND date = %s AND time_out IS NOT NULL
        """, (employee_id, today))
        record = cursor.fetchone()
        cursor.close()
        conn.close()
        return record is not None
    except Error as e:
        print("❌ Database error in has_time_out_today:", e)
        return False


def ensure_daily_attendance_rows(target_date):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO attendance (date, employee_id, fullname, status)
        SELECT %s, e.employee_id, e.name, 'Present'
        FROM employees e
        WHERE e.status = 'Active'
          AND e.employee_id NOT IN (
              SELECT employee_id FROM attendance WHERE date = %s
          )
    """, (target_date, target_date))

    conn.commit()
    cursor.close()
    conn.close()

def mark_absent_employees():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        today = datetime.now().date()
        cutoff_time = dtime(17, 0)  # 5 PM

        if datetime.now().time() < cutoff_time:
            print("⏳ Too early.")
            return

        # ✅ Ensure rows exist FIRST
        ensure_daily_attendance_rows(today)

        # ✅ Mark absent where no time-in
        cursor.execute("""
            UPDATE attendance
            SET status = 'Absent'
            WHERE date = %s
              AND time_in IS NULL
              AND status = 'Present'
        """, (today,))

        affected = cursor.rowcount
        conn.commit()

        if affected == 0:
            print("✅ No absentees today.")
        else:
            print(f"🚫 Marked {affected} employee(s) as Absent.")

    except Error as e:
        print("❌ Error:", e)

    finally:
        cursor.close()
        conn.close()


