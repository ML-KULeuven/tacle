from flask import Flask, render_template, request, redirect
from engine.util import TempFile
import workflow

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('table.html')

@app.route("/feedback",methods=["POST"])
def handle_constraints():
    if 'csv_data' not in request.form or 'tables_json' not in request.form:
      return "invalid request"
    else:
      csv_file    = TempFile(request.form['csv_data'], "csv")
      tables_file = TempFile(request.form['tables_json'], "json")
      solutions = workflow.main(csv_file.name, tables_file.name, False)
      return display_solutions(solutions)
#TODO

@app.route('/testpost')
def test_post():
  return render_template('test.html')


def display_solutions(solutions):
    str_repr = ""
    for constraint in solutions.solutions:
        for solution in solutions.get_solutions(constraint):
           str_repr += constraint.to_string(solution) + "\n" 
    return str_repr



if __name__ == "__main__":
    app.run()
