from flask import Flask, render_template, redirect, flash, request, jsonify, session, url_for, jsonify
from models import db, Applicant, Recruiter, Interview, Task, Job, Company, Applied, connect_db
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, UserAddForm, UserEditForm, AddIntForm, NewTaskFormRec, NewTaskFormApp, RecruiterEditForm, NewCompanyForm, NewJobForm, ApplyForm




app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ats'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'itsasecret'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_ECHO'] = True 
app.debug = True

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if 'user_type' in session:
        if session['user_type'] == 'applicant':
            return Applicant.query.get(int(user_id))
        elif session['user_type'] == 'recruiter':
            return Recruiter.query.get(int(user_id))
    return None


connect_db(app)



# First Entry Page -- contains Login and Sign Up

@app.route("/")
def home():
    return render_template('index.html')




@app.route("/login", methods=["GET", "POST"])
def login():
     ### "Login Form"     
    form = LoginForm()
    if request.method == 'POST':
        applicant = Applicant.query.filter_by(username=form.username.data).first()
        password = request.form.get('password')
       
        if applicant and check_password_hash(applicant.password, password):
                    login_user(applicant)
                    session['user_type'] = 'applicant'
                    flash(f"Login Successful! {applicant.username}", "success")
                    return redirect(f"/users")
        else:
           flash("Invalid username or password!", "error")
           return redirect("/login")
                
    return render_template('login.html', form=form)



@app.route("/signup", methods=["POST", "GET"])
def signup():
    ### "Sign up Form"
    form = UserAddForm()
    if request.method == 'POST' and form.validate_on_submit():
            password = request.form.get('password')

            new_app = Applicant(username = form.username.data,
                password = generate_password_hash(password, method='sha256'), first_name = form.first_name.data,
                last_name = form.last_name.data, phone = form.phone.data,
                email = form.email.data, job_title = form.job_title.data,)

            db.session.add(new_app)
            db.session.commit()  
            flash("Successful signup!", "success")
            return redirect("/login")
    return render_template('signup.html', form=form)



@app.route('/logout')
@login_required
def logout():
    """Handle logout of user."""
    logout_user()
    session.clear() 
    flash("LOGGED OUT!", 'success')
    return redirect("/login")




### Applicant pages after login

@app.route("/users")
@login_required
def applicant_homepage():
    #  "User login to own specific page by ID "
    applicant = current_user
    form = NewTaskFormApp()
    companies = Company.query.order_by(Company.name).all()
    jobs = Job.query.order_by(Job.title).all()
 #   interviews = Interview.query.filter_by(applicant=applicant.id).all()
    task = Task.query.filter_by(applicant_id=applicant.id).all()
   

    return render_template('user/user_homepage.html', applicant=applicant,
                           companies=companies, 
                           jobs=jobs, task=task, form=form)


@app.route("/users/newtask", methods=["POST", "GET"])
@login_required
def user_new_task():
    applicant = current_user
    form = NewTaskFormApp()
    task = Task.query.filter_by(applicant_id=applicant.id).all()
    if request.method == 'POST':
            new_task = Task(notes=form.notes.data, applicant_id=applicant.id)

            db.session.add(new_task)
            db.session.commit()  
            flash("New Task Added!", "success")
            return redirect(f"/users")
    return render_template('user/user_homepage.html', task=task, applicant=applicant, 
                           form=form)


@app.route("/users/<int:task_id>")
@login_required
def task_view():
    #  "User login to own specific page by ID "
    applicant = current_user
    companies = Company.query.order_by(Company.name).all()
    jobs = Job.query.order_by(Job.title).all()
 #   interviews = Interview.query.filter_by(applicant=applicant.id).all()
    task = Task.query.filter_by(applicant_id=applicant.id).all()

    return render_template('user/taskview.html', applicant=applicant,
                           companies=companies, 
                           jobs=jobs, task=task)



@app.route("/users/<int:task_id>/delete/", methods=["POST, GET"])
@login_required
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':    
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully.", "success")
        return redirect(url_for('applicant_homepage'))
    

@app.route("/users/jobs")
@login_required
def jobs():
    """Jobs route for current user"""
    jobs = Job.query.order_by(Job.company_id).all()
    applicant = current_user
    interviews = Interview.query.filter_by(application_id=applicant.id).all()
    companies = Company.query.order_by(Company.id).all()

    if request.method == "POST":
        job_id = request.form.get("job_id")
        job = Job.query.get_or_404(job_id)
        new_application = Applied(application_id=applicant.id, job_id=job_id)
        db.session.add(new_application)
        db.session.commit()
        return jsonify({"message": f"Applied to job: {job.title}"})
    return render_template('user/jobs.html', jobs=jobs, applicant=applicant, interviews=interviews, companies=companies)

@app.route("/users/jobs/apply", methods=["POST","GET"])
@login_required
def jobs_apply():
    """Jobs route for current user"""
    companies = Company.query.order_by(Company.id).all()
    form = ApplyForm()
    job_id = form.job_id.data
    application_id = current_user.id
 #   company_id = form.company_id.data

    if form.validate_on_submit():
        new_application = Applied(application_id=application_id, job_id=job_id) #, company_id=company_id)
        db.session.add(new_application)
        db.session.commit()
        return redirect(f"/users/jobs")
    return render_template('user/jobs_apply.html', job_id=job_id, application_id=application_id, companies=companies,
                           form=form)


@app.route("/users/companies")
@login_required
def company():
    """Companies route for user"""
    companies = Company.query.order_by(Company.name).all()
    jobs = Job.query.order_by(Job.title).all()
    applicant = current_user
    return render_template('user/companies.html', companies=companies, jobs=jobs, applicant=applicant)


@app.route("/users/interview", methods=["POST", "GET"])
@login_required
def new_interview():
    """Add new Interview"""
    applicant = current_user
    companies = Company.query.order_by(Company.name).all()
    form = AddIntForm()
    if request.method == 'POST' and form.validate_on_submit():
        new_interview = Interview(application_id=applicant.id, job_id=form.job_id.data, notes=form.notes.data)
        db.session.add(new_interview)
        db.session.commit()
        flash("New Interview added!", "success")
        return redirect("/users")
    return render_template('user/new_interview.html', applicant=applicant,
                           companies=companies,
                           form=form)




## Profile Form / Edit / Delete

@app.route("/users/profile")
@login_required
def profile_form():
    """current use profile view"""
    applicant = current_user
    return render_template('user/profile_form.html', applicant=applicant)




@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    applicant = current_user
    form = UserEditForm(obj=applicant)
    if form.validate_on_submit():
        applicant.username = form.username.data
        applicant.first_name = form.first_name.data
        applicant.last_name = form.last_name.data
        applicant.phone = form.phone.data
        applicant.email = form.email.data
        applicant.job_title = form.job_title.data
        db.session.commit()
        flash(f"{applicant.username}'s profile has been updated!", "success")
        return redirect("/users")
    return render_template("user/edit_profile.html", form=form, applicant=applicant)



### Mater Account/Recruiter pages after login

@app.route("/master/<int:recruiter_id>")
@login_required
def master_determine(recruiter_id):
    recruiter = current_user
    applicant = Applicant.query.order_by(Applicant.last_name, Applicant.first_name, Applicant.email, Applicant.id, Applicant.username, Applicant.password, Applicant.phone, Applicant.job_title).all()
    companies = Company.query.order_by(Company.id).all()
    jobs = Job.query.order_by(Job.title).all()
    interviews = Interview.query.order_by(Interview.notes, Interview.id).all()
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    apply = Applied.query.order_by(Applied.job_id)
    task = Task.query.filter_by(recruiter_id=recruiter_id).all()
    call_recruiter = Recruiter.query.order_by(Recruiter.first_name, Recruiter.last_name).all()

    return render_template('master/master_homepage.html', recruiter=recruiter, applicant=applicant, companies=companies, interviews=interviews, 
                           jobs=jobs, apply=apply, task=task, call_recruiter=call_recruiter)


@app.route("/master/login", methods=["GET", "POST"])
def master_login():
 ### Master Login Form     
    form = LoginForm()
    if request.method == 'POST':
        recruiter = Recruiter.query.filter_by(username=form.username.data).first()
        password = request.form.get('password')
        try:
            if recruiter:
                if check_password_hash(recruiter.password, password):
                    login_user(recruiter)
                    session['user_type'] = 'recruiter'
                    flash(f"Login Successful! {recruiter.username}", "success")
                    return redirect(f"master/{recruiter.id}")
            
            else:
                flash("Invalid username!", "error")
                return redirect("/master/login")  
        except:
           flash("Invalid username or password!", "error")
           return redirect("/master/login")

    return render_template('master/master_log.html', form=form)


@app.route("/master/<int:recruiter_id>/newtask", methods=["POST", "GET"])
@login_required
def master_new_task(recruiter_id):
    recruiter = Recruiter.query.get(recruiter_id)
    form = NewTaskFormRec()
    task = Task.query.filter_by(recruiter_id=recruiter_id).all()
    if request.method == 'POST':
            notes = request.form.get('notes')
            new_task = Task(notes = notes, recruiter_id = recruiter.id)
            db.session.add(new_task)
            db.session.commit()  
            flash("New Task Added!", "success")
            return redirect(f"/master/{recruiter.id}")
    return render_template('master/master_homepage.html', task=task, recruiter=recruiter, 
                           form=form)



@app.route("/master/<int:recruiter_id>/applied", methods=["POST", "GET"])
@login_required
def master_applies(recruiter_id):
    recruiter = Recruiter.query.get(recruiter_id)
    apply = Applied.query.order_by(Applied.job_id).all()
    task = Task.query.filter_by(recruiter_id=recruiter_id).all()

    return render_template('master/master_applied.html', task=task, recruiter=recruiter, 
                           apply=apply)



@app.route("/master/<int:applicant_id>/delete", methods=["GET", "POST"])
@login_required
def applicant_delete(applicant_id):
    recruiter = current_user
    applicant = Applicant.query.get_or_404(applicant_id)
    if request.method == 'POST':
        db.session.delete(applicant)
        db.session.commit()
        flash("Applicant deleted successfully.", "success")
        return redirect(url_for('master_profile', recruiter_id=recruiter.id))
    

@app.route("/master/<int:task_id>/delete", methods=["POST"])
@login_required
def task_delete_master(task_id):
    task = Task.query.get_or_404(task_id)
    recruiter_id = current_user.id
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully.", "success")
    return redirect(url_for('master_determine', recruiter_id=recruiter_id))


@app.route("/master/companies/<int:company_id>/delete", methods=["GET", "POST"])
@login_required
def company_delete(company_id):
    recruiter = current_user
    company = Company.query.get_or_404(company_id)
    if request.method == 'POST':
        db.session.delete(company)
        db.session.commit()
        flash("Company deleted successfully.", "success")
        return redirect(url_for('master_companies',recruiter_id=recruiter.id))

    

@app.route("/master/jobs/<int:job_id>/delete", methods=["GET, POST"])
@login_required
def job_delete(job_id):
    recruiter = current_user
    avail_job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        db.session.delete(avail_job)
        db.session.commit()
        flash("Jobs deleted successfully.", "success")
        return redirect(url_for('master_jobs', recruiter_id=recruiter.id))

    

@app.route("/master/<int:recruiter_id>/jobs")
@login_required
def master_jobs(recruiter_id):
    jobs = Job.query.order_by(Job.company_id).all()
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    return render_template('master/master_jobs.html', recruiter=recruiter, jobs=jobs)


@app.route("/master/<int:recruiter_id>/companies")
@login_required
def master_companies(recruiter_id):
    recruiter_id = current_user.id
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    companies = Company.query.order_by(Company.name).all()

    return render_template('master/master_companies.html',recruiter=recruiter, 
                            companies=companies)


@app.route("/master/<int:recruiter_id>/profile")
@login_required
def master_profile(recruiter_id):
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    call_recruiters = Recruiter.query.order_by(Recruiter.first_name, Recruiter.last_name).all()
    applicants = Applicant.query.order_by(Applicant.last_name, Applicant.first_name).all()
    companies = Company.query.order_by(Company.name).all()
    jobs = Job.query.order_by(Job.title).all()
    interviews = Interview.query.order_by(Interview.notes, Interview.id).all()
    return render_template('master/master_profile.html', recruiter=recruiter, applicants=applicants, companies=companies, 
                           interviews=interviews, jobs=jobs, call_recruiters=call_recruiters, recruiter_id=recruiter_id)


@app.route("/master/<int:recruiter_id>/profile/edit", methods=["GET", "POST"])
@login_required
def edit_recruiter_profile(recruiter_id):
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    recruiter = current_user
    form = RecruiterEditForm(obj=recruiter)
    if form.validate_on_submit():
        recruiter.username = form.username.data
        recruiter.first_name = form.first_name.data
        recruiter.last_name = form.last_name.data
        recruiter.email = form.email.data
        db.session.commit()
        flash(f"{recruiter.username}'s profile has been updated!", "success")
        return redirect(f"master/{recruiter.id}")
    return render_template("master/edit_profile.html", form=form, recruiter=recruiter)


@app.route("/master/<int:recruiter_id>/profile/newrecruiter", methods=["POST", "GET"])
@login_required
def master_new_recruiter(recruiter_id):
    form = RecruiterEditForm()
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    app = Applicant.query.order_by(Applicant.username)
    companies = Company.query.order_by(Company.location)
    password = request.form.get('password')

    if request.method == 'POST':
        new_recruiter = Recruiter(username = form.username.data,
                 password = generate_password_hash(password, method='sha256'), first_name = form.first_name.data,
                 last_name = form.last_name.data, email = form.email.data)

        db.session.add(new_recruiter)
        db.session.commit()  
        flash("New Recruiter added!", "success")
        return redirect(f"/master/{recruiter.id}/profile")
    return render_template('master/master_new_recruiter.html', recruiter=recruiter, app=app, companies=companies, 
                           form=form)




@app.route("/master/<int:recruiter_id>/profile/newapp", methods=["POST", "GET"])
@login_required
def master_new_app(recruiter_id):
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    app = Applicant.query.order_by(Applicant.username)
    form = UserAddForm()
    password = request.form.get('password')
    if request.method == 'POST':

            new_app = Applicant(username = form.username.data,
                password = generate_password_hash(password, method='sha256'), first_name = form.first_name.data,
                last_name = form.last_name.data, phone = form.phone.data,
                email = form.email.data, job_title = form.job_title.data,)

            db.session.add(new_app)
            db.session.commit()  
            flash("New Applicant Added!", "success")
            return redirect(f"/master/{recruiter.id}")
    return render_template('master/master_new_app.html', recruiter=recruiter, app=app, 
                           form=form)


@app.route("/master/<int:recruiter_id>/profile/newcompanies", methods=["POST", "GET"])
@login_required
def master_new_companies(recruiter_id):
    form = NewCompanyForm()
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    app = Applicant.query.order_by(Applicant.username)
    companies = Company.query.order_by(Company.location)

    if request.method == 'POST':
        new_comp = Company(name=form.name.data, 
                            industry=form.industry.data, location=form.location.data)

        db.session.add(new_comp)
        db.session.commit()  
        flash("New Companies added!", "success")
        return redirect(f"/master/{recruiter.id}/companies")
    return render_template('master/master_new_company.html', recruiter=recruiter, app=app, companies=companies, 
                           form=form)


@app.route('/apply_job', methods=['POST'])
def apply_job():
    data = request.get_json()
    job_id = data.get('job_id')
    applicant_id = current_user

    # Process the application (save to database, etc.)
    # Example:
    applied = Applied(applicant_id=applicant_id, job_id=job_id)
    db.session.add(applied)
    db.session.commit()

    return jsonify({'message': 'Application successful!'})


@app.route("/master/<int:recruiter_id>/profile/newjob", methods=["POST", "GET"])
@login_required
def master_new_job(recruiter_id):
    form = NewJobForm()
    recruiter = Recruiter.query.get_or_404(recruiter_id)

    if request.method == 'POST':
        new_job = Job(title=form.title.data, salary=form.salary.data,
                      company_id = form.company_id.data)

        db.session.add(new_job)
        db.session.commit()  
        flash("New Job added!", "success")
        return redirect(f"/master/{recruiter.id}/jobs")
    return render_template('master/master_new_job.html', recruiter=recruiter,
                           form=form)




@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run()