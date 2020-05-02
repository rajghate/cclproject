# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 13:11:18 2020

@author: rajmugdha
"""


from flask import Flask,render_template,redirect,request,flash,send_file,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug import secure_filename
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import shutil
from zipfile import ZipFile


app=Flask(__name__)
app.config['UPLOAD_FOLDER']='Files/'
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///app.db'
db=SQLAlchemy(app)

error=""
not_allowed_extensions=['png','mp3','mp4','jpeg','pdf']

class fileList(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    filename=db.Column(db.String(200),nullable=False)
    date_uploaded=db.Column(db.DateTime,default=datetime.utcnow)
    owner=db.Column(db.String(200))	
    visitors=db.Column(db.String(1000))
    def __repr__(self):
       return '<Task %r>' % self.id
   
class user(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(200))
    uname=db.Column(db.String(200))
    password=db.Column(db.String(200))
    urole=db.Column(db.String(100))
    
    def __repr__(self):
       return '<user %r>' % self.id

class message(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sender=db.Column(db.String(200))
    reciever=db.Column(db.String(200))
    content=db.Column(db.String(500))
    category=db.Column(db.String(200))
    filename=db.Column(db.String(200))
    def __repr__(self):
       return '<msg %r>' % self.id

db.create_all()

def generate_cipher():
    key=os.urandom(24)
    iv_des=os.urandom(8)
    iv_aes=os.urandom(16)
    iv_camellia=os.urandom(16)
    return key,iv_des,iv_aes,iv_camellia

def hybrid_data_encrption(filename,chunks):
    datalist=[]
    j=0
    key,iv_des,iv_aes,iv_camellia=generate_cipher()
    aes=Cipher(algorithm=algorithms.AES(key), mode=modes.CTR(iv_aes), backend=default_backend())
    tdes=Cipher(algorithm=algorithms.TripleDES(key), mode=modes.OFB(iv_des), backend=default_backend())
    camellia=Cipher(algorithm=algorithms.Camellia(key), mode=modes.CTR(iv_camellia), backend=default_backend())
    aes_enc=aes.encryptor()
   
    tdes_enc=tdes.encryptor()
   
    cam_enc=camellia.encryptor()
    filepaths=[]
   
    with open(filename.split(".")[0]+"_"+"key"+".txt","wb") as file:
        filepaths.append(filename.split(".")[0]+"_"+"key"+".txt")
        file.write(key)
    with open(filename.split(".")[0]+"_"+"iv1"+".txt","wb") as file:
        filepaths.append(filename.split(".")[0]+"_"+"iv1"+".txt")
        file.write(iv_aes)
    with open(filename.split(".")[0]+"_"+"iv2"+".txt","wb") as file:
        filepaths.append(filename.split(".")[0]+"_"+"iv2"+".txt")
        file.write(iv_des)
    with open(filename.split(".")[0]+"_"+"iv3"+".txt","wb") as file:
        filepaths.append(filename.split(".")[0]+"_"+"iv3"+".txt")
        file.write(iv_camellia)
    with ZipFile(filename.split(".")[0]+".zip","w") as zip:
        for file in filepaths:
            zip.write(file)
            os.remove(file)
    with open(filename,"r") as file:
        lines=file.readlines()
        linenum=len(lines)
        for i in range(0,chunks):
            if i==chunks-1:
                data="".join(lines[j:linenum])
            else:
                data="".join(lines[j:j+(linenum//chunks)])
            j=j+(linenum//chunks)
            datalist.append(data)
    ct=[]
    ct.append(aes_enc.update(datalist[0].encode(encoding="utf-8"))+aes_enc.finalize())
    ct.append(tdes_enc.update(datalist[1].encode(encoding="utf-8"))+tdes_enc.finalize())
    ct.append(cam_enc.update(datalist[2].encode(encoding="utf-8"))+cam_enc.finalize())
    return key,ct,aes,tdes,camellia

    
def file_encryption(filename):
    key,ct,aes,tdes,camellia=hybrid_data_encrption(filename, 3)
    os.remove(filename)
    for i in range(3):
        part_name=filename.split(".")[0]+"part_"+str(i)+"."+filename.split(".")[1]
        with open(part_name,"wb") as file:
            file.write(ct[i])
    return aes,tdes,camellia
def decrypt_from_file(filename,aes,tdes,camellia):
    pt=[]
    aes_dc=aes.decryptor()
    tdes_dc=tdes.decryptor()
    cam_dc=camellia.decryptor()
    for i in range(3):
        part_name=filename.split(".")[0]+"part_"+str(i)+"."+filename.split(".")[1]
        with open(part_name,"rb") as file:
            data=file.read()
            if i==0:
                pt.append(aes_dc.update(data)+aes_dc.finalize())
            if i==1:
                pt.append(tdes_dc.update(data)+tdes_dc.finalize())
            if i==2:
                pt.append(cam_dc.update(data)+cam_dc.finalize())
    s=""
    for i in range(3):
        s=s+pt[i].decode("utf-8")
    return(s)          

def decrypt(filename,filedir):
    keyfile=filedir+"/"+filename+"_"+"key"+".txt"
    iv1=filedir+"/"+filename+"_"+"iv1"+".txt"
    iv2=filedir+"/"+filename+"_"+"iv2"+".txt"
    iv3=filedir+"/"+filename+"_"+"iv3"+".txt"
    with open(keyfile,"rb") as file:
        key=file.read()
    os.remove(keyfile)
    with open(iv1,"rb") as file:
        iv_aes=file.read()
    with open(iv2,"rb") as file:
        iv_des=file.read()
    with open(iv3,"rb") as file:
        iv_cam=file.read()
    os.remove(iv1)
    os.remove(iv2)
    os.remove(iv3)
    print(key)
    aes=Cipher(algorithm=algorithms.AES(key), mode=modes.CTR(iv_aes), backend=default_backend())
    tdes=Cipher(algorithm=algorithms.TripleDES(key), mode=modes.OFB(iv_des), backend=default_backend())
    camellia=Cipher(algorithm=algorithms.Camellia(key), mode=modes.CTR(iv_cam), backend=default_backend())
    aes_dc=aes.decryptor()
    tdes_dc=tdes.decryptor()
    cam_dc=camellia.decryptor()
    pt=[]
    for i in range(3):
        part_name=filedir+"/"+filename+"part_"+str(i)+"."+"txt"
        with open(part_name,"rb") as file:
            data=file.read()
            if i==0:
                pt.append(aes_dc.update(data)+aes_dc.finalize())
            if i==1:
                pt.append(tdes_dc.update(data)+tdes_dc.finalize())
            if i==2:
                pt.append(cam_dc.update(data)+cam_dc.finalize())
    s=""
    for i in range(3):
        s=s+pt[i].decode("utf-8")
    return(s)            
                

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['psw']
        userdetails=user.query.filter_by(email=email).first()
        if userdetails.email==email and userdetails.password==password:
            session['uname']=userdetails.uname
            session['urole']=userdetails.urole
            session['message']=None
            return redirect('/')
        
    return render_template('login.html')

@app.route('/newuser',methods=['GET','POST'])
def newuser():
    if request.method=='POST':   
        uname=request.form['uname']
        email=request.form['email']
        password=request.form['password']
        users=user.query.filter_by(email=email,uname=uname).first()
        if users: return'email or uname already in use'
        role=str(request.form.get('role'))
        print(role)
        newuser=user(email=email,uname=uname,password=password,urole=role)
        db.session.add(newuser)
        db.session.commit()        
        return redirect('/')
    if 'uname' in session:
       return render_template('newuser.html',name=session['uname'],urole=session['urole'],error=error)
    else:
       return render_template('newuser.html')                
@app.route('/')
def home():
   tasks= fileList.query.order_by(fileList.date_uploaded).all()
   if 'uname' in session:
       return render_template('home.html',tasks=tasks,uname=session['uname'],urole=session['urole'],error=error)
   else:
       return redirect('/login')


@app.route('/upload')
def upload_file():
   if 'uname' in session:
       return render_template('upload.html',uname=session['uname'],urole=session['urole'])
   else:
       return redirect('/login')
 

	
@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
   if request.method == 'POST' and request.files['file']:
      print(1)
      f = request.files['file']
      print(f)
      filename = secure_filename(f.filename)
      ext=f.filename.split(".")[1]
      name=f.filename.split(".")[0]
      newname=name+"."+"txt"
      if ext in not_allowed_extensions:
          error='We are not providing security for these extension'
          return redirect('/upload',error=error)
      os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'],name))
      newdir=os.path.join(app.config['UPLOAD_FOLDER'],name)
      f.save(os.path.join(newdir, newname))
      task_content=filename
      new_task=fileList(filename=task_content,owner=session['uname'],visitors="")
      try:
         db.session.add(new_task)
         db.session.commit()
      except:
         return 'error'
      aes,tdes,camellia=file_encryption(os.path.join(newdir, newname))
      print(decrypt_from_file(os.path.join(newdir, newname), aes, tdes, camellia))
      return redirect('/')
   else:
       return redirect('/upload')


@app.route('/delete/<int:id>')
def delete(id):
    task_do_delete=fileList.query.get_or_404(id)
    print(task_do_delete)
	
    db.session.delete(task_do_delete)
    db.session.commit()
    shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'],task_do_delete.filename.split(".")[0]))
    return redirect('/')        

@app.route('/view/<int:id>',methods=['GET','POST'])
def view(id):
    task=fileList.query.get_or_404(id)
    filedir=os.path.join(app.config['UPLOAD_FOLDER'],task.filename.split(".")[0])
    data="".encode('utf-8')
    if request.method=='POST' :
        fkzip=request.files['keyzip']
        path=os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(fkzip.filename))
        fkzip.save(path)
        with ZipFile(path,"r") as zip:
            zip.extractall()
        os.remove(path)
        data=decrypt(task.filename.split(".")[0], filedir)
        decrypted=True
    else:
        for i in os.listdir(filedir):
            with open(filedir+"/"+i,"rb") as file:
                data=data+file.read()
        decrypted=False
            
    if 'uname' in session:
       return render_template('view.html',task=task,uname=session['uname'],urole=session['urole'],data=data,decrypted=decrypted)
    else:
       return redirect('/login')


@app.route('/downloader/<int:id>')
def download(id):
    task=fileList.query.get_or_404(id)
    newdir=app.config['UPLOAD_FOLDER']+"/"+task.filename.split(".")[0]
    path=os.path.join(newdir, task.filename.split(".")[0]+".zip")
    
    return send_file(path,cache_timeout=-1,as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('uname',None)
    session.pop('urole',None)
    return redirect('/login')




@app.route('/request/<int:id>')
def keyrequest(id):
    task=fileList.query.get_or_404(id)
    tasks=fileList.query.order_by(fileList.date_uploaded).all()
    filename=task.filename
    sender=session['uname']
    reciever=task.owner
    content=sender+" has requested key for file "+filename
    newmsg=message(sender=sender,reciever=reciever,content=content,category="keyreq",filename=filename)
    db.session.add(newmsg)
    db.session.commit()
    error="Request sent"
    return render_template('home.html',tasks=tasks,uname=session['uname'],urole=session['urole'],error=error)

@app.route('/profile')
def profile():
    rcvmsgs=message.query.filter_by(reciever=session['uname'],category="res").all()
    sndmsgs=message.query.filter_by(reciever=session['uname'],category="keyreq").all()
    files=fileList.query.filter_by(owner=session['uname']).all()
    users=user.query.filter_by(urole="normal").all()
    
    return render_template('profile.html',rcvmsgs=rcvmsgs,sndmsgs=sndmsgs,files=files,users=users,uname=session['uname'],urole=session['urole'])
    
@app.route('/accept/<int:id>')
def accreq(id):
    msg=message.query.get_or_404(id)
    sender=msg.sender
    filename=msg.filename
    file=fileList.query.filter_by(filename=filename).first()
    if msg.category=="keyreq":
        file.visitors=file.visitors+"+"+sender
        content="Request Accepted Get Your Key Now"
        newmsg=message(sender=session['uname'],reciever=sender,content=content,category="res",filename=filename)
        db.session.add(newmsg)
    db.session.delete(msg)
    db.session.commit()
    return redirect('/')

@app.route('/reject/<int:id>')
def rejreq(id):
    msg=message.query.get_or_404(id)
    if msg.category=="keyreq":
        content="Request Denied"
        newmsg=message(sender=session['uname'],reciever=msg.sender,content=content,category="res",filename=msg.filename)
        db.session.add(newmsg)
    
    db.session.delete(msg)
    db.session.commit()
    return redirect('/profile')

@app.route('/deluser/<int:id>')
def deluser(id):
    user_to_delete=user.query.get_or_404(id)
    db.session.delete(user_to_delete)
    db.session.commit()
    return redirect('/profile')
    

if __name__ == '__main__':
    app.run()

