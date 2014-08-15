from flask import Flask
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test@localhost/mangarecs'
db = SQLAlchemy(app)

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    recommender = db.Column(db.Text)

    def __init__(self, name, recommender):
        self.name = name
        self.recommender = recommender

    def __repr__(self):
        return '<Manga: %r>' % self.name


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def recs_post():
    text = request.form['text']
    text = text.replace(' ', '_')
    return redirect(url_for('recommendations', manga_name=text))

@app.route('/recs/<manga_name>')
def recommendations(manga_name):
    manga_name = manga_name.replace('_', ' ')
    users = Manga.query.filter_by(name=manga_name).all()
    users = [user.recommender for user in users]
    manga = Manga.query.filter(Manga.recommender.in_(users)).filter(Manga.name!=manga_name).all()
    recs = [item.name for item in manga]
    return render_template('recommendations.html', manga_name=manga_name, recs=recs)

@app.route('/commonrecs/<manga_name>')
def common_recommendations(manga_name):
    manga_name = manga_name.replace('_', ' ')
    users = Manga.query.filter_by(name=manga_name).all()
    users = [user.recommender for user in users]
    manga = Manga.query.filter(Manga.recommender.in_(users)).filter(Manga.name!=manga_name).all()
    recs = [item.name for item in manga]
    array = []
    for x in recs:
        if (recs.count(x) > 1 and array.count(x) == 0):
            array.append(x)
    return render_template('recommendations.html', manga_name=manga_name, recs=array)

if __name__ == '__main__':
    app.run(debug=True);
