from flask import Flask, render_template, request
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('table.html')

@app.route("/handle_constraints",methods=["POST"])
def handle_constraints():
    if request.method == 'POST':
      print(request.files['file'])
      if 'csv_data' not in request.files or 'tables_json' not in request.files:
        return "file is missing"
    else:
      return redirect("/")
#TODO

@app.route('/testpost')
def test_post():
  return render_template('test.html')

if __name__ == "__main__":
    app.run()
