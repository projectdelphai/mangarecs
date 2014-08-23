from flask import Flask
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import distinct
from sqlalchemy import func,desc,asc
import os

app = Flask(__name__)
if "DATABASE_URL" in os.environ:
    engine = create_engine(os.environ['DATABASE_URL'], echo=True)
else:
    engine = create_engine('postgresql://test:test@localhost/mangarecs', echo=True)

Base = declarative_base()
class Manga(Base):
    __tablename__ = 'manga'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    recommender = Column(Text)

    def __repr__(self):
        return "<Manga(name='%s', recommender='%s')>" % (self.name, self,recommender)

Session = sessionmaker(bind=engine)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recs')
def recs_index_without_trailing_slash():
    return redirect(url_for('recs_index'))

@app.route('/commonrecs')
def common_recs_index_without_trailing_slash():
    return redirect(url_for('common_recs_index'))

@app.route('/recs/')
def recs_index():
    return render_template('recs.html', type='recs')

@app.route('/recs/', methods=['POST'])
def recs_post():
    text = request.form['text']
    text = text.replace(' ', '_')
    return redirect(url_for('recommendations', manga_name=text))

@app.route('/commonrecs/')
def common_recs_index():
    return render_template('recs.html', type='commonrecs')

@app.route('/commonrecs/', methods=['POST'])
def common_recs_post():
    text = request.form['text']
    text = text.replace(' ', '_')
    return redirect(url_for('common_recommendations', manga_name=text))

@app.route('/recs/<manga_name>')
def recommendations(manga_name):
    session = Session()
    manga_name = manga_name.replace('_', ' ')
    users = session.query(Manga.recommender).filter(func.lower(Manga.name)==manga_name.lower()).all()
    manga = session.query(Manga.name, func.count(Manga.name) ).filter(Manga.recommender.in_(users), Manga.name != manga_name).group_by(Manga.name).order_by(func.count(Manga.name)).all()
    print(manga)
    recs = [item.name for item in manga]
    recs.reverse()
    return render_template('recommendations.html', manga_name=manga_name, recs=recs)

@app.route('/commonrecs/<manga_name>')
def common_recommendations(manga_name):
    session = Session()
    manga_name = manga_name.replace('_', ' ')
    users = session.query(Manga.recommender).filter(func.lower(Manga.name)==manga_name.lower()).all()
    manga = session.query(Manga.name).filter(Manga.recommender.in_(users), Manga.name != manga_name).all()
    recs = [item.name for item in manga]
    array = []
    for x in recs:
        if (recs.count(x) > 1 and array.count(x) == 0):
            array.append(x)
    return render_template('recommendations.html', manga_name=manga_name, recs=array)

if __name__ == '__main__':
    app.run(debug=True);
