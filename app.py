from flask import Flask, render_template, request, redirect
import sqlite3
import datetime
import math
import qrcode
import os

app = Flask(__name__)

TOTAL_SLOTS = 5


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# FIXED SLOT ALLOCATION FUNCTION
def get_available_slot():

    conn = get_db_connection()

    occupied = conn.execute(
        "SELECT slot FROM parking WHERE exit_time IS NULL"
    ).fetchall()

    occupied_slots = [int(row["slot"]) for row in occupied]

    conn.close()

    for slot in range(1, TOTAL_SLOTS + 1):
        if slot not in occupied_slots:
            return slot

    return None


@app.route('/')
def index():

    msg = request.args.get("msg")

    conn = get_db_connection()

    vehicles = conn.execute(
        "SELECT * FROM parking ORDER BY id DESC"
    ).fetchall()

    occupied = conn.execute(
        "SELECT COUNT(*) FROM parking WHERE exit_time IS NULL"
    ).fetchone()[0]

    available = TOTAL_SLOTS - occupied

    today_count = conn.execute(
        "SELECT COUNT(*) FROM parking WHERE date(entry_time)=date('now')"
    ).fetchone()[0]

    revenue = conn.execute(
        "SELECT SUM(fee) FROM parking WHERE date(exit_time)=date('now')"
    ).fetchone()[0]

    if revenue is None:
        revenue = 0

    occupied_slots_data = conn.execute(
        "SELECT slot FROM parking WHERE exit_time IS NULL"
    ).fetchall()

    occupied_slots = [int(row["slot"]) for row in occupied_slots_data]

    slot_map = []

    for i in range(1, TOTAL_SLOTS + 1):

        if i in occupied_slots:
            slot_map.append({"slot": i, "status": "occupied"})
        else:
            slot_map.append({"slot": i, "status": "free"})

    conn.close()

    return render_template(
        "index.html",
        vehicles=vehicles,
        available=available,
        total=TOTAL_SLOTS,
        today_count=today_count,
        revenue=revenue,
        slot_map=slot_map,
        msg=msg
    )


@app.route('/add', methods=['GET', 'POST'])
def add_vehicle():

    conn = get_db_connection()

    occupied = conn.execute(
        "SELECT COUNT(*) FROM parking WHERE exit_time IS NULL"
    ).fetchone()[0]

    available = TOTAL_SLOTS - occupied

    if request.method == 'POST':

        vehicle = request.form['vehicle']

        existing_vehicle = conn.execute(
            "SELECT * FROM parking WHERE vehicle=? AND exit_time IS NULL",
            (vehicle,)
        ).fetchone()

        if existing_vehicle:
            conn.close()
            return "Vehicle already parked!"

        slot = get_available_slot()

        if slot is None:
            conn.close()
            return "Parking Full!"

        entry_time = datetime.datetime.now()

        conn.execute(
            "INSERT INTO parking(vehicle,slot,entry_time) VALUES (?,?,?)",
            (vehicle,slot,entry_time)
        )

        conn.commit()

        # QR Code generation
        qr_data = f"Vehicle:{vehicle} Slot:{slot}"

        img = qrcode.make(qr_data)

        os.makedirs("static/qrcodes", exist_ok=True)

        img.save(f"static/qrcodes/{vehicle}.png")

        conn.close()

        return redirect('/?msg=Vehicle Parked Successfully')

    conn.close()

    return render_template("entry.html", available=available)


@app.route('/exit/<int:id>')
def exit_vehicle(id):

    exit_time = datetime.datetime.now()

    conn = get_db_connection()

    vehicle = conn.execute(
        "SELECT entry_time FROM parking WHERE id=?",
        (id,)
    ).fetchone()

    entry_time = datetime.datetime.fromisoformat(vehicle["entry_time"])

    minutes = (exit_time - entry_time).seconds / 60

    hours = math.ceil(minutes / 60)

    fee = hours * 20

    conn.execute(
        "UPDATE parking SET exit_time=?, fee=? WHERE id=?",
        (exit_time, fee, id)
    )

    conn.commit()
    conn.close()

    return redirect('/?msg=Vehicle Exit Completed')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)