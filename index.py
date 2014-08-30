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
import config
import os

app = Flask(__name__)
app.config.from_object(config)
if "DATABASE_URL" in os.environ:
    engine = create_engine(os.environ['DATABASE_URL'], echo_pool=True, pool_size=20, max_overflow=0)
else:
    engine = create_engine('postgresql://test:test@localhost/mangarecs')

Base = declarative_base()
class Manga(Base):
    __tablename__ = 'manga'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    recommender = Column(Text)
    mu_id = Column(Integer)
    mu_name = Column(Text)
    level = Column(Text)

    def __repr__(self):
        return "<Manga(name='%s', recommender='%s')>" % (self.name, self,recommender)

class Signup(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)
    email = Column(Text)

    def __repr__(self):
        return "<Signup(email='%s')>" % (self.email)

Session = sessionmaker(bind=engine)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def signup():
    email = request.form['signup']
    session = Session()
    signup = Signup(email=email)
    session.add(signup)
    session.commit()
    session.close()
    return render_template('signup_confirmation.html')

@app.route('/recs')
def recs_index_without_trailing_slash():
    return redirect(url_for('recs_index'))

@app.route('/commonrecs')
def common_recs_index_without_trailing_slash():
    return redirect(url_for('common_recs_index'))

@app.route('/recs/')
def recs_index():
    session = Session()
    beginner = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Beginner').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    intermediate = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Intermediate').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    advanced = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Advanced').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    session.close()
    return render_template('recs.html', type='recs', beginner_recs=beginner, intermediate_recs=intermediate, advanced_recs=advanced)

@app.route('/recs/', methods=['POST'])
def recs_post():
    text = request.form['text']
    text = text.replace(' ', '_')
    return redirect(url_for('recommendations', manga_name=text))

@app.route('/commonrecs/')
def common_recs_index():
    session = Session()
    beginner = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Beginner').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    intermediate = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Intermediate').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    advanced = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Advanced').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    session.close()
    return render_template('recs.html', type='commonrecs', beginner_recs=beginner, intermediate_recs=intermediate, advanced_recs=advanced)

@app.route('/commonrecs/', methods=['POST'])
def common_recs_post():
    text = request.form['text']
    text = text.replace(' ', '_')
    return redirect(url_for('common_recommendations', manga_name=text))

@app.route('/recs/<manga_name>')
def recommendations(manga_name):
    session = Session()
    manga_name = manga_name.replace('_', ' ')
    users = session.query(Manga.name, Manga.recommender).filter(func.lower(Manga.name)==manga_name.lower()).all()
    if len(users) == 0:
        first_manga = session.query(Manga.name, func.levenshtein(Manga.name, manga_name,2,1,4)).filter(func.levenshtein(Manga.name, manga_name,2,1,4)<15).order_by(asc(func.levenshtein(Manga.name, manga_name,2,1,4))).first()
        if first_manga:
            users = session.query(Manga.name, Manga.recommender).filter(Manga.name==first_manga.name).all()
            manga_name = users[0].name
        else:
            users = []
    else:
        manga_name = users[0].name
    users = [item.recommender for item in users]
    manga = session.query(Manga.name, Manga.mu_id, func.count(Manga.name) ).filter(Manga.recommender.in_(users), func.lower(Manga.name) != manga_name.lower()).group_by(Manga.name, Manga.mu_id).order_by(func.random()).all()
    session.close()
    recs = []
    for item in manga:
        if item[2] == 1:
            if item.mu_id:
                recs.append([item.name, item.mu_id])
            else:
                recs.append([item.name, 0])
    recs.reverse()
    return render_template('recommendations.html', manga_name=manga_name, recs=recs)

@app.route('/commonrecs/<manga_name>')
def common_recommendations(manga_name):
    manga_name = manga_name.replace('_', ' ')
    session = Session()
    users = session.query(Manga.name, Manga.recommender).filter(func.lower(Manga.name)==manga_name.lower()).all()
    if len(users) == 0:
        first_manga = session.query(Manga.name, func.levenshtein(Manga.name, manga_name,2,1,4)).filter(func.levenshtein(Manga.name, manga_name,2,1,4)<15).order_by(asc(func.levenshtein(Manga.name, manga_name,2,1,4))).first()
        if first_manga:
            users = session.query(Manga.name, Manga.recommender).filter(Manga.name==first_manga.name).all()
            manga_name = users[0].name
        else:
            users = []
    else:
        manga_name = users[0].name
    users = [item.recommender for item in users]
    manga = session.query(Manga.name, Manga.mu_id).filter(Manga.recommender.in_(users), func.lower(Manga.name) != manga_name.lower()).order_by(func.random()).all()
    session.close()
    recs = [item.name for item in manga]
    ids = [item.mu_id for item in manga]
    i=0
    array = []
    array2 = []
    for x in recs:
        if (recs.count(x) > 1 and array2.count(x) == 0):
            array.append([x, ids[i]])
            array2.append(x)
        i += 1
    return render_template('recommendations.html', manga_name=manga_name, recs=array)

if __name__ == '__main__':
    app.run(debug=True);
