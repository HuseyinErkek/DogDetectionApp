from flask import Flask ,render_template

app = Flask(__name__)

@app.route('/')
def home():  # put application's code here
    return render_template('index.html')

@app.route('/index.html')
def index():
    return render_template('index.html')
@app.route('/camera.html')
def camera():
    return render_template('camera.html')
@app.route('/howto.html')
def howto():
    return render_template("howto.html")

@app.route('/upload.html')
def upload():
    return render_template("upload.html")

if __name__ == '__main__':
    app.run()
