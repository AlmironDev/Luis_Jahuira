from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app.models import VideoSource
from app.forms import VideoSourceForm
from app.utils.posture_detector import PostureDetector
from app import db
import cv2

main_bp = Blueprint('main', __name__)

# Variable global para el detector (en producción usaría un sistema más robusto)
current_detector = None

@main_bp.route('/')
def index():
    active_video = VideoSource.query.filter_by(is_active=True).first()
    return render_template('index.html', active_video=active_video)

@main_bp.route('/video_feed')
def video_feed():
    global current_detector
    
    active_video = VideoSource.query.filter_by(is_active=True).first()
    if not active_video:
        return "No hay video activo", 404
    
    if current_detector is None or current_detector.video_source != active_video.video_url:
        if current_detector:
            del current_detector
        current_detector = PostureDetector(active_video.video_url)
    
    def generate():
        while True:
            frame = current_detector.get_frame()
            if frame is None:
                continue
                
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    return Response(generate(),
                  mimetype='multipart/x-mixed-replace; boundary=frame')

@main_bp.route('/videos')
def video_list():
    videos = VideoSource.query.all()
    return render_template('video_list.html', videos=videos)

@main_bp.route('/add_video', methods=['GET', 'POST'])
def add_video():
    form = VideoSourceForm()
    if form.validate_on_submit():
        # Desactivar todos los videos antes de activar uno nuevo
        if form.is_active.data:
            VideoSource.query.update({'is_active': False})
            db.session.commit()
        
        video = VideoSource(
            name=form.name.data,
            video_url=form.video_url.data,
            is_active=form.is_active.data
        )
        db.session.add(video)
        db.session.commit()
        flash('Video agregado correctamente', 'success')
        return redirect(url_for('main.video_list'))
    return render_template('add_video.html', form=form)

@main_bp.route('/edit_video/<int:id>', methods=['GET', 'POST'])
def edit_video(id):
    video = VideoSource.query.get_or_404(id)
    form = VideoSourceForm(obj=video)
    
    if form.validate_on_submit():
        # Desactivar todos los videos antes de activar uno nuevo
        if form.is_active.data:
            VideoSource.query.update({'is_active': False})
            db.session.commit()
        
        form.populate_obj(video)
        db.session.commit()
        flash('Video actualizado correctamente', 'success')
        return redirect(url_for('main.video_list'))
    
    return render_template('edit_video.html', form=form, video=video)

@main_bp.route('/delete_video/<int:id>')
def delete_video(id):
    video = VideoSource.query.get_or_404(id)
    db.session.delete(video)
    db.session.commit()
    flash('Video eliminado correctamente', 'success')
    return redirect(url_for('main.video_list'))

@main_bp.route('/set_active/<int:id>')
def set_active(id):
    # Desactivar todos los videos primero
    VideoSource.query.update({'is_active': False})
    db.session.commit()
    
    # Activar el video seleccionado
    video = VideoSource.query.get_or_404(id)
    video.is_active = True
    db.session.commit()
    
    flash(f'Video "{video.name}" activado correctamente', 'success')
    return redirect(url_for('main.video_list'))