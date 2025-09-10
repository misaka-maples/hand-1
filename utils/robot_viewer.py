from flask import Flask, render_template
import threading
import time
import webbrowser

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("test.html")

def open_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:8000", new=2)

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(port=8000,debug=False)
