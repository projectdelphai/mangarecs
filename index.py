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
from sqlalchemy import func,desc,asc, and_
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
    type = Column(Text)
    level = Column(Text)
    completed = Column(Text)
    demographic = Column(Text)

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
    session = Session()
    beginner_recs = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Beginner').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    intermediate_recs = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Intermediate').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    advanced_recs = session.query(Manga.name, Manga.mu_id, func.count(Manga.name)).filter(Manga.level == 'Advanced').group_by(Manga.name, Manga.mu_id).order_by(func.random()).limit(5).all()
    session.close()
    return render_template('index.html', beginner_recs=beginner_recs,intermediate_recs=intermediate_recs,advanced_recs=advanced_recs)

@app.route('/', methods=['POST'])
def index_post():
   form = request.form['submit']
   if form == 'Search':
       options = request.form.getlist("options")
       sametype = False
       samegenre = False
       commonrecs = False
       if "sametype" in options:
           sametype = True
       if "samegenre" in options:
           samegenre = True
       if "commonrecs" in options:
           commonrecs = True
       text = request.form['text'].replace(' ', '_')
       return redirect(url_for('recommendations', manga_name=text, sametype=sametype, samegenre=samegenre, commonrecs=commonrecs))
   elif form == 'Signup':
       email = request.form['signup']
       if "@" not in email:
           return render_template('signup_failed.html')
       session = Session()
       signup = Signup(email=email)
       session.add(signup)
       session.commit()
       session.close()
       return render_template('signup_confirmation.html')

@app.route('/recs/<manga_name>')
def recommendations(manga_name):
    sametype = request.args.get('sametype')
    samegenre = request.args.get('samegenre')
    commonrecs = request.args.get('commonrecs')
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
    manga_details = session.query(Manga.type, Manga.demographic).filter(Manga.name == manga_name).first()
    type = manga_details[0]
    demographic = manga_details[1]
    users = [item.recommender for item in users]
    if commonrecs == "True":
        raw_manga = session.query(Manga.name, Manga.mu_id).filter(Manga.recommender.in_(users), func.lower(Manga.name) != manga_name.lower()).order_by(func.random())
    else:
        raw_manga = session.query(Manga.name, Manga.mu_id, func.count(Manga.name) ).filter(and_(Manga.recommender.in_(users), func.lower(Manga.name) != manga_name.lower())).group_by(Manga.name, Manga.mu_id).order_by(func.random())
    if sametype == "True":
        raw_manga = raw_manga.filter(Manga.type == type)
    if samegenre == "True":
        raw_manga = raw_manga.filter(Manga.demographic == demographic)
    manga = raw_manga.all()
    session.close()
    if commonrecs == "True":
        raw_recs = [item.name for item in manga]
        ids = [item.mu_id for item in manga]
        i=0
        recs = []
        array2 = []
        for x in raw_recs:
            if (raw_recs.count(x) > 1 and array2.count(x) == 0):
                recs.append([x, ids[i]])
                array2.append(x)
            i += 1
    else:
        recs = []
        for item in manga:
            if item[2] == 1:
                if item.mu_id:
                    recs.append([item.name, item.mu_id])
                else:
                    recs.append([item.name, 0])
        recs.reverse()
    return render_template('recommendations.html', manga_name=manga_name, recs=recs)

if __name__ == '__main__':
    app.run(debug=True);
