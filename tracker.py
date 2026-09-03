import sqlite3
import math
import time
from pynput import mouse

# Calibration Constants
DPI = 1000
MM_PER_INCH = 25.4
PIXELS_PER_MM = DPI / MM_PER_INCH

# Temporary memory for the current second
state = {"last_x": None, "last_y": None, "distance": 0.0, "scroll": 0.0}

# Initialize the database
db = sqlite3.connect('mouse_data.db', check_same_thread=False)
db.execute('CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, distance REAL, scroll REAL)')
db.execute('INSERT OR IGNORE INTO stats (id, distance, scroll) VALUES (1, 0, 0)')
db.commit()

def on_move(x, y):
    if state["last_x"] is not None:
        dx = x - state["last_x"]
        dy = y - state["last_y"]
        # Euclidean distance math
        state["distance"] += math.sqrt(dx**2 + dy**2) / PIXELS_PER_MM
    state["last_x"], state["last_y"] = x, y

def on_scroll(x, y, dx, dy):
    # Assume each scroll wheel notch is ~2mm of physical rotation
    state["scroll"] += abs(dy) * 2.0  

# Hook into the OS mouse events in the background
listener = mouse.Listener(on_move=on_move, on_scroll=on_scroll)
listener.start()

print("🚀 Hardware tracking started. Move your mouse...")

# The main loop: Save to database every 1 second
try:
    while True:
        # Add the last second of movement to the grand total in the DB
        db.execute('UPDATE stats SET distance = distance + ?, scroll = scroll + ? WHERE id = 1', 
                  (state["distance"], state["scroll"]))
        db.commit()
        
        # Fetch the grand total to display in the terminal
        cursor = db.execute('SELECT distance, scroll FROM stats WHERE id = 1')
        total_dist, total_scroll = cursor.fetchone()
        
        print(f"Desk Distance: {total_dist:.2f} mm | Wheel Distance: {total_scroll:.2f} mm", end='\r')
        
        # Reset the temporary counters
        state["distance"] = 0.0
        state["scroll"] = 0.0
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTracking stopped.")