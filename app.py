from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Contact(db.Model):
    """Model for storing contact form submissions"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'message': self.message,
            'submitted_at': self.submitted_at.isoformat()
        }

class Project(db.Model):
    """Model for storing portfolio projects"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    project_url = db.Column(db.String(300))
    github_url = db.Column(db.String(300))
    technologies = db.Column(db.String(500))  # Comma-separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'project_url': self.project_url,
            'github_url': self.github_url,
            'technologies': self.technologies.split(',') if self.technologies else [],
            'created_at': self.created_at.isoformat()
        }

class Skill(db.Model):
    """Model for storing skills"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Frontend, Backend, Tools
    proficiency = db.Column(db.Integer)  # 1-100
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'proficiency': self.proficiency
        }

# Routes
@app.route('/')
def index():
    """Serve the main portfolio page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Contact API
@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submissions"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create new contact record
        contact = Contact(
            name=data.get('name'),
            email=data.get('email'),
            message=data.get('message')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact saved successfully',
            'id': contact.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contact submissions"""
    contacts = Contact.query.order_by(Contact.submitted_at.desc()).all()
    return jsonify([contact.to_dict() for contact in contacts])

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a contact submission"""
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Contact deleted'})

# Projects API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        if not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        project = Project(
            title=data.get('title'),
            description=data.get('description'),
            image_url=data.get('image_url'),
            project_url=data.get('project_url'),
            github_url=data.get('github_url'),
            technologies=','.join(data.get('technologies', []))
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        project.title = data.get('title', project.title)
        project.description = data.get('description', project.description)
        project.image_url = data.get('image_url', project.image_url)
        project.project_url = data.get('project_url', project.project_url)
        project.github_url = data.get('github_url', project.github_url)
        if 'technologies' in data:
            project.technologies = ','.join(data.get('technologies', []))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'project': project.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Project deleted'})

# Skills API
@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Get all skills"""
    skills = Skill.query.all()
    return jsonify([skill.to_dict() for skill in skills])

@app.route('/api/skills/<category>', methods=['GET'])
def get_skills_by_category(category):
    """Get skills by category"""
    skills = Skill.query.filter_by(category=category).all()
    return jsonify([skill.to_dict() for skill in skills])

@app.route('/api/skills', methods=['POST'])
def create_skill():
    """Create a new skill"""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('category'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        skill = Skill(
            name=data.get('name'),
            category=data.get('category'),
            proficiency=data.get('proficiency', 50)
        )
        
        db.session.add(skill)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Skill created successfully',
            'skill': skill.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
