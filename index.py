from flask import Flask,request,redirect,url_for,render_template
from sqlalchemy import create_engine,func,desc,asc,and_,distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Text
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

@app.route('/about.html')
def help():
    return render_template('about.html')

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
       sametype = True if "sametype" in options else False
       samegenre = True if "samegenre" in options else False
       commonrecs = True if "commonrecs" in options else False
       
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
    common_manga = session.query(Manga.name, Manga.mu_id, Manga.type, Manga.demographic, func.count(Manga.name)).filter(Manga.recommender.in_(users), func.lower(Manga.name) != manga_name.lower()).group_by(Manga.name, Manga.mu_id, Manga.type, Manga.demographic).having(func.count(Manga.name) > 1).order_by(func.random()).all()
    long_manga = session.query(Manga.name, Manga.mu_id, Manga.type, Manga.demographic, func.count(Manga.name) ).filter(and_(Manga.recommender.in_(users), func.lower(Manga.name) != manga_name.lower())).group_by(Manga.name, Manga.mu_id, Manga.type, Manga.demographic).having(func.count(Manga.name) == 1).order_by(func.random()).all()
    manga_details = session.query(Manga.type, Manga.demographic).filter(Manga.name == manga_name).first()
    session.close()
    
    type = manga_details[0]
    demographic = manga_details[1]
    checked = [ sametype, samegenre, commonrecs ]
 
    recs=[]
    for item in common_manga:
        recs.append([item.name, item.type, item.demographic, item.mu_id, "common"])
    for item in long_manga:
        recs.append([item.name, item.type, item.demographic, item.mu_id, "long"])
    
    return render_template('recommendations.html', manga_name=manga_name, recs=recs, checked=checked, type=type, demographic=demographic)

if __name__ == '__main__':
    app.run(debug=True);
